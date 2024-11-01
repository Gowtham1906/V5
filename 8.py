import subprocess
import os
import json
import boto3
from typing import Dict, List, Any
import sys
import time

def fetch_vpc_resources(vpc_ids: List[str], region: str) -> Dict[str, Dict]:
    """Fetch all VPC and associated resource details."""
    ec2_client = boto3.client('ec2', region_name=region)
    resource_details = {}

    for vpc_id in vpc_ids:
        resource_details[vpc_id] = {
            'vpc': {},
            'subnets': [],
            'internet_gateways': [],
            'nat_gateways': [],
            'security_groups': [],
            'route_tables': []
        }

        # Fetch VPC details with error handling
        try:
            vpc_response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
            vpc = vpc_response['Vpcs'][0]
            vpc_details = {
                'cidr_block': vpc['CidrBlock'],
                'tags': {tag['Key']: tag['Value'] for tag in vpc.get('Tags', [])},
                'enable_dns_support': True,
                'enable_dns_hostnames': True
            }
            resource_details[vpc_id]['vpc'] = vpc_details
        except Exception as e:
            print(f"Error fetching VPC details: {str(e)}")
            continue

        try:
            # Fetch Subnets
            paginator = ec2_client.get_paginator('describe_subnets')
            for page in paginator.paginate(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]):
                for subnet in page['Subnets']:
                    subnet_details = {
                        'id': subnet['SubnetId'],
                        'cidr_block': subnet['CidrBlock'],
                        'availability_zone': subnet['AvailabilityZone'],
                        'map_public_ip': subnet.get('MapPublicIpOnLaunch', False),
                        'tags': {tag['Key']: tag['Value'] for tag in subnet.get('Tags', [])}
                    }
                    resource_details[vpc_id]['subnets'].append(subnet_details)

            # Fetch Internet Gateways
            igw_response = ec2_client.describe_internet_gateways(
                Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}]
            )
            for igw in igw_response['InternetGateways']:
                igw_details = {
                    'id': igw['InternetGatewayId'],
                    'tags': {tag['Key']: tag['Value'] for tag in igw.get('Tags', [])},
                    'vpc_id': vpc_id
                }
                resource_details[vpc_id]['internet_gateways'].append(igw_details)

            # Fetch NAT Gateways
            paginator = ec2_client.get_paginator('describe_nat_gateways')
            for page in paginator.paginate(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]):
                for nat in page['NatGateways']:
                    if nat['State'] != 'deleted':
                        nat_details = {
                            'id': nat['NatGatewayId'],
                            'subnet_id': nat['SubnetId'],
                            'allocation_id': next((addr['AllocationId'] for addr in nat['NatGatewayAddresses']), None),
                            'tags': {tag['Key']: tag['Value'] for tag in nat.get('Tags', [])},
                            'vpc_id': vpc_id
                        }
                        resource_details[vpc_id]['nat_gateways'].append(nat_details)

            # Fetch Security Groups
            paginator = ec2_client.get_paginator('describe_security_groups')
            for page in paginator.paginate(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]):
                for sg in page['SecurityGroups']:
                    sg_details = {
                        'id': sg['GroupId'],
                        'name': sg['GroupName'],
                        'description': sg['Description'],
                        'tags': {tag['Key']: tag['Value'] for tag in sg.get('Tags', [])},
                        'ingress_rules': sg.get('IpPermissions', []),
                        'egress_rules': sg.get('IpPermissionsEgress', []),
                        'vpc_id': vpc_id
                    }
                    resource_details[vpc_id]['security_groups'].append(sg_details)

            # Fetch Route Tables
            paginator = ec2_client.get_paginator('describe_route_tables')
            for page in paginator.paginate(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]):
                for rt in page['RouteTables']:
                    rt_details = {
                        'id': rt['RouteTableId'],
                        'tags': {tag['Key']: tag['Value'] for tag in rt.get('Tags', [])},
                        'routes': [
                            {
                                'destination': route.get('DestinationCidrBlock', route.get('DestinationIpv6CidrBlock', '')),
                                'target': next((v for k, v in route.items() if k.endswith('Id') and v), None),
                                'state': route.get('State', 'active')
                            }
                            for route in rt.get('Routes', [])
                        ],
                        'associations': [
                            {
                                'id': assoc['RouteTableAssociationId'],
                                'subnet_id': assoc.get('SubnetId'),
                                'main': assoc.get('Main', False)
                            }
                            for assoc in rt.get('Associations', [])
                        ],
                        'vpc_id': vpc_id
                    }
                    resource_details[vpc_id]['route_tables'].append(rt_details)

        except Exception as e:
            print(f"Error fetching resources: {str(e)}")

    return resource_details

def create_terraform_files(parent_module: str, child_module: str):
    """Create minimal Terraform files focusing on VPC and Subnet resources."""
    parent_variables_tf = """
variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "vpc_configs" {
  description = "VPC configurations"
  type = map(object({
    cidr_block           = string
    enable_dns_support   = bool
    enable_dns_hostnames = bool
    tags                 = map(string)
  }))
}

variable "subnet_configs" {
  description = "Subnet configurations"
  type = map(object({
    vpc_id                  = string
    cidr_block             = string
    availability_zone      = string
    map_public_ip          = bool
    tags                   = map(string)
  }))
}

variable "igw_configs" {
  description = "Internet Gateway configurations"
  type = map(object({
    vpc_id = string
    tags   = map(string)
  }))
}

variable "nat_configs" {
  description = "NAT Gateway configurations"
  type = map(object({
    subnet_id = string
    tags      = map(string)
  }))
}

variable "sg_configs" {
  description = "Security Group configurations"
  type = map(object({
    name        = string
    description = string
    vpc_id      = string
    ingress     = list(object({
      from_port   = number
      to_port     = number
      protocol    = string
      cidr_blocks = list(string)
    }))
    egress      = list(object({
      from_port   = number
      to_port     = number
      protocol    = string
      cidr_blocks = list(string)
    }))
    tags        = map(string)
  }))
}

variable "rt_configs" {
  description = "Route Table configurations"
  type = map(object({
    vpc_id  = string
    routes  = list(object({
      destination_cidr_block = string
      gateway_id            = string
    }))
    tags    = map(string)
  }))
}"""

    parent_main_tf = """
provider "aws" {
  region = var.aws_region
}

resource "aws_vpc" "imported_vpc" {
  for_each = var.vpc_configs
  
  cidr_block           = each.value.cidr_block
  enable_dns_support   = each.value.enable_dns_support
  enable_dns_hostnames = each.value.enable_dns_hostnames
  tags                 = each.value.tags
}

resource "aws_subnet" "imported_subnet" {
  for_each = var.subnet_configs
  
  vpc_id                  = each.value.vpc_id
  cidr_block             = each.value.cidr_block
  availability_zone      = each.value.availability_zone
  map_public_ip_on_launch = each.value.map_public_ip
  tags                   = each.value.tags
}

# Internet Gateway Resource
resource "aws_internet_gateway" "imported_igw" {
  for_each = var.igw_configs
  
  vpc_id = each.value.vpc_id
  tags   = each.value.tags
}

# NAT Gateway Resource
resource "aws_nat_gateway" "imported_nat" {
  for_each = var.nat_configs
  
  subnet_id = each.value.subnet_id
  tags      = each.value.tags
}

# Security Group Resource
resource "aws_security_group" "imported_sg" {
  for_each = var.sg_configs
  
  name        = each.value.name
  description = each.value.description
  vpc_id      = each.value.vpc_id
  tags        = each.value.tags

  dynamic "ingress" {
    for_each = each.value.ingress
    content {
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
    }
  }

  dynamic "egress" {
    for_each = each.value.egress
    content {
      from_port   = egress.value.from_port
      to_port     = egress.value.to_port
      protocol    = egress.value.protocol
      cidr_blocks = egress.value.cidr_blocks
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Route Table Resource
resource "aws_route_table" "imported_rt" {
  for_each = var.rt_configs
  
  vpc_id = each.value.vpc_id
  tags   = each.value.tags

  dynamic "route" {
    for_each = each.value.routes
    content {
      cidr_block = route.value.destination_cidr_block
      gateway_id = route.value.gateway_id
    }
  }
}"""

    child_main_tf = """
module "vpc_resources" {
  source = "../Parent_Module"

  aws_region     = var.aws_region
  vpc_configs    = var.vpc_configs
  subnet_configs = var.subnet_configs
  igw_configs    = var.igw_configs
  nat_configs    = var.nat_configs
  sg_configs     = var.sg_configs
  rt_configs     = var.rt_configs
}"""

    child_variables_tf = """
variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "vpc_configs" {
  description = "VPC configurations"
  type = map(object({
    cidr_block           = string
    enable_dns_support   = bool
    enable_dns_hostnames = bool
    tags                 = map(string)
  }))
}

variable "subnet_configs" {
  description = "Subnet configurations"
  type = map(object({
    vpc_id                  = string
    cidr_block             = string
    availability_zone      = string
    map_public_ip          = bool
    tags                   = map(string)
  }))
}

variable "igw_configs" {
  description = "Internet Gateway configurations"
  type = map(object({
    vpc_id = string
    tags   = map(string)
  }))
}

variable "nat_configs" {
  description = "NAT Gateway configurations"
  type = map(object({
    subnet_id = string
    tags      = map(string)
  }))
}

variable "sg_configs" {
  description = "Security Group configurations"
  type = map(object({
    name        = string
    description = string
    vpc_id      = string
    ingress     = list(object({
      from_port   = number
      to_port     = number
      protocol    = string
      cidr_blocks = list(string)
    }))
    egress      = list(object({
      from_port   = number
      to_port     = number
      protocol    = string
      cidr_blocks = list(string)
    }))
    tags        = map(string)
  }))
}

variable "rt_configs" {
  description = "Route Table configurations"
  type = map(object({
    vpc_id  = string
    routes  = list(object({
      destination_cidr_block = string
      gateway_id            = string
    }))
    tags    = map(string)
  }))
}"""

    # Create directories and files
    for path, content in [
        (os.path.join(parent_module, "variables.tf"), parent_variables_tf),
        (os.path.join(parent_module, "main.tf"), parent_main_tf),
        (os.path.join(child_module, "main.tf"), child_main_tf),
        (os.path.join(child_module, "variables.tf"), child_variables_tf),
    ]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content.strip())

def create_tfvars(child_module: str, resource_details: Dict, region: str):
    """Create or update terraform.tfvars with new VPC configurations while preserving existing ones."""
    tfvars_path = os.path.join(child_module, "terraform.tfvars")
    existing_configs = {
        'vpc_configs': {},
        'subnet_configs': {},
        'igw_configs': {},
        'nat_configs': {},
        'sg_configs': {},
        'rt_configs': {}
    }

    # Read existing configurations if file exists
    if os.path.exists(tfvars_path):
        try:
            with open(tfvars_path, 'r') as f:
                content = f.read()
                # Parse existing configurations using string manipulation
                for config_type in existing_configs.keys():
                    start_marker = f"{config_type} = "
                    end_marker = "\n\n"
                    if start_marker in content:
                        start_idx = content.index(start_marker) + len(start_marker)
                        end_idx = content.find(end_marker, start_idx)
                        if end_idx == -1:  # If it's the last configuration
                            config_str = content[start_idx:].strip()
                        else:
                            config_str = content[start_idx:end_idx].strip()
                        try:
                            existing_configs[config_type] = json.loads(config_str)
                        except json.JSONDecodeError:
                            print(f"Warning: Could not parse existing {config_type}")
                            existing_configs[config_type] = {}
        except Exception as e:
            print(f"Warning: Error reading existing tfvars file: {str(e)}")

    # Process new configurations
    vpc_configs = {}
    subnet_configs = {}
    igw_configs = {}
    nat_configs = {}
    sg_configs = {}
    rt_configs = {}

    for vpc_id, resources in resource_details.items():
        # VPC Configuration
        vpc_configs[vpc_id] = resources['vpc']

        # Subnet Configurations
        for subnet in resources['subnets']:
            subnet_id = subnet['id']
            subnet_configs[subnet_id] = {
                'vpc_id': vpc_id,
                'cidr_block': subnet['cidr_block'],
                'availability_zone': subnet['availability_zone'],
                'map_public_ip': subnet['map_public_ip'],
                'tags': subnet['tags']
            }
        
        # IGW Configurations
        for igw in resources['internet_gateways']:
            igw_id = igw['id']
            igw_configs[igw_id] = {
                'vpc_id': vpc_id,
                'tags': igw['tags']
            }

        # NAT Configurations
        for nat in resources['nat_gateways']:
            nat_id = nat['id']
            nat_configs[nat_id] = {
                'subnet_id': nat['subnet_id'],
                'tags': nat['tags']
            }

        # Security Group Configurations
        for sg in resources['security_groups']:
            sg_id = sg['id']
            
            # Process ingress rules with safe defaults
            processed_ingress = []
            try:
                raw_ingress = sg.get('ingress_rules', [])
                for rule in raw_ingress:
                    processed_rule = {
                        'from_port': int(rule.get('FromPort', 0)) if rule.get('FromPort') is not None else 0,
                        'to_port': int(rule.get('ToPort', 0)) if rule.get('ToPort') is not None else 0,
                        'protocol': rule.get('IpProtocol', '-1'),
                        'cidr_blocks': [ip_range.get('CidrIp', '0.0.0.0/0') for ip_range in rule.get('IpRanges', [])]
                    }
                    
                    if not processed_rule['cidr_blocks']:
                        processed_rule['cidr_blocks'] = ['0.0.0.0/0']
                        
                    processed_ingress.append(processed_rule)
            except Exception as e:
                print(f"Warning: Error processing ingress rules for SG {sg_id}: {str(e)}")

            # Process egress rules with safe defaults
            processed_egress = []
            try:
                raw_egress = sg.get('egress_rules', [])
                if not raw_egress:
                    processed_egress = [{
                        'from_port': 0,
                        'to_port': 0,
                        'protocol': '-1',
                        'cidr_blocks': ['0.0.0.0/0']
                    }]
                else:
                    for rule in raw_egress:
                        processed_rule = {
                            'from_port': int(rule.get('FromPort', 0)) if rule.get('FromPort') is not None else 0,
                            'to_port': int(rule.get('ToPort', 0)) if rule.get('ToPort') is not None else 0,
                            'protocol': rule.get('IpProtocol', '-1'),
                            'cidr_blocks': [ip_range.get('CidrIp', '0.0.0.0/0') for ip_range in rule.get('IpRanges', [])]
                        }
                        
                        if not processed_rule['cidr_blocks']:
                            processed_rule['cidr_blocks'] = ['0.0.0.0/0']
                            
                        processed_egress.append(processed_rule)
            except Exception as e:
                print(f"Warning: Error processing egress rules for SG {sg_id}: {str(e)}")

            sg_configs[sg_id] = {
                'name': sg.get('name', f'sg-{sg_id}'),
                'description': sg.get('description', 'Managed by Terraform'),
                'vpc_id': vpc_id,
                'ingress': processed_ingress,
                'egress': processed_egress,
                'tags': sg.get('tags', {})
            }

        # Route Table Configurations
        for rt in resources['route_tables']:
            rt_id = rt['id']
            processed_routes = []
            
            for route in rt['routes']:
                if route['destination'] and route['target']:
                    processed_routes.append({
                        'destination_cidr_block': route['destination'],
                        'gateway_id': route['target']
                    })
            
            rt_configs[rt_id] = {
                'vpc_id': vpc_id,
                'routes': processed_routes,
                'tags': rt['tags']
            }

    # Merge existing and new configurations
    merged_configs = {
        'vpc_configs': {**existing_configs['vpc_configs'], **vpc_configs},
        'subnet_configs': {**existing_configs['subnet_configs'], **subnet_configs},
        'igw_configs': {**existing_configs['igw_configs'], **igw_configs},
        'nat_configs': {**existing_configs['nat_configs'], **nat_configs},
        'sg_configs': {**existing_configs['sg_configs'], **sg_configs},
        'rt_configs': {**existing_configs['rt_configs'], **rt_configs}
    }

    # Write merged configurations to tfvars file
    tfvars_content = f"""aws_region = "{region}"

vpc_configs = {json.dumps(merged_configs['vpc_configs'], indent=2)}

subnet_configs = {json.dumps(merged_configs['subnet_configs'], indent=2)}

igw_configs = {json.dumps(merged_configs['igw_configs'], indent=2)}

nat_configs = {json.dumps(merged_configs['nat_configs'], indent=2)}

sg_configs = {json.dumps(merged_configs['sg_configs'], indent=2)}

rt_configs = {json.dumps(merged_configs['rt_configs'], indent=2)}
"""

    with open(tfvars_path, 'w') as f:
        f.write(tfvars_content)

def run_terraform_command(command: List[str], cwd: str, timeout: int = 300) -> bool:
    """Run Terraform command with timeout and better error handling."""
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )

        print(f"\nExecuting: {' '.join(command)}")
        
        start_time = time.time()
        while True:
            if process.poll() is not None:
                break
            
            if time.time() - start_time > timeout:
                process.terminate()
                print(f"Command timed out after {timeout} seconds")
                return False
            
            output = process.stdout.readline()
            error = process.stderr.readline()
            
            if output:
                print(output.strip())
            if error:
                print(f"ERROR: {error.strip()}", file=sys.stderr)
            
            time.sleep(0.1)

        return_code = process.poll()
        return return_code == 0

    except Exception as e:
        print(f"Error executing Terraform command: {str(e)}")
        return False

def import_resources(child_module: str, resource_details: Dict):
    """Import VPC and Subnet resources with improved error handling."""
    try:
        os.chdir(child_module)
        
        # Initialize Terraform with backend configuration
        if not run_terraform_command(['terraform', 'init'], child_module):
            raise Exception("Terraform initialization failed")

        # Import VPCs first
        for vpc_id in resource_details.keys():
            print(f"\nImporting VPC {vpc_id}...")
            if not run_terraform_command([
                'terraform', 'import',
                f'module.vpc_resources.aws_vpc.imported_vpc["{vpc_id}"]',
                vpc_id
            ], child_module):
                print(f"Warning: Failed to import VPC {vpc_id}")
                continue

            # Import associated subnets
            for subnet in resource_details[vpc_id]['subnets']:
                subnet_id = subnet['id']
                print(f"Importing Subnet {subnet_id}...")
                run_terraform_command([
                    'terraform', 'import',
                    f'module.vpc_resources.aws_subnet.imported_subnet["{subnet_id}"]',
                    subnet_id
                ], child_module)
                
            # Import Internet Gateways
            for igw in resource_details[vpc_id]['internet_gateways']:
                igw_id = igw['id']
                print(f"\nImporting Internet Gateway {igw_id}...")
                import_cmd = [
                    'terraform', 'import',
                    f'module.vpc_resources.aws_internet_gateway.imported_igw["{igw_id}"]',
                    igw_id
                ]
                run_terraform_command(import_cmd, child_module)

            # Import NAT Gateways
            for nat in resource_details[vpc_id]['nat_gateways']:
                nat_id = nat['id']
                print(f"\nImporting NAT Gateway {nat_id}...")
                import_cmd = [
                    'terraform', 'import',
                    f'module.vpc_resources.aws_nat_gateway.imported_nat["{nat_id}"]',
                    nat_id
                ]
                run_terraform_command(import_cmd, child_module)

            # Import Security Groups
            for sg in resource_details[vpc_id]['security_groups']:
                sg_id = sg['id']
                print(f"\nImporting Security Group {sg_id}...")
                import_cmd = [
                    'terraform', 'import',
                    f'module.vpc_resources.aws_security_group.imported_sg["{sg_id}"]',
                    sg_id
                ]
                run_terraform_command(import_cmd, child_module)

            # Import Route Tables
            for rt in resource_details[vpc_id]['route_tables']:
                rt_id = rt['id']
                print(f"\nImporting Route Table {rt_id}...")
                import_cmd = [
                    'terraform', 'import',
                    f'module.vpc_resources.aws_route_table.imported_rt["{rt_id}"]',
                    rt_id
                ]
                run_terraform_command(import_cmd, child_module)

        # Final plan with reduced complexity
        # print("\nRunning final Terraform plan...")
        # if run_terraform_command(['terraform', 'plan'], child_module):
        #     print("\nApplying Terraform changes...")
        #     run_terraform_command(['terraform', 'apply'], child_module)
            
    except Exception as e:
        print(f"Error during import: {str(e)}")
    finally:
        os.chdir(os.path.dirname(child_module))

def main():
    """Main function with improved error handling and simplified resource management."""
    try:
        base_path = os.path.abspath(os.path.dirname(__file__))
        parent_module = os.path.join(base_path, "Parent_Module")
        child_module = os.path.join(base_path, "Child_Module")
        
        # Configuration
        region = "us-east-1"
        vpc_ids = ["vpc-055b2e670d7bfdace"]  # Add your new VPC IDs here  "vpc-008e46fde5ccc685a"
        
        # Create Terraform files only if they don't exist
        if not os.path.exists(parent_module) or not os.path.exists(child_module):
            print("Creating Terraform files...")
            create_terraform_files(parent_module, child_module)
        
        # Fetch VPC details
        print("Fetching VPC details...")
        resource_details = fetch_vpc_resources(vpc_ids, region)
        
        # Create/Update tfvars
        print("Updating terraform.tfvars...")
        create_tfvars(child_module, resource_details, region)
        
        # Import resources
        print("Importing resources...")
        import_resources(child_module, resource_details)
        
    except Exception as e:
        print(f"Error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
