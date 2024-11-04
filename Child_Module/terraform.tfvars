aws_region = "us-east-1"

vpc_configs = {
  "vpc-0deb766aa06396f05": {
    "cidr_block": "172.17.0.0/16",
    "tags": {
      "Name": "Terra-Auto-vpc"
    },
    "enable_dns_support": true,
    "enable_dns_hostnames": true
  }
}

subnet_configs = {
  "subnet-013c13bc11dbd80b1": {
    "vpc_id": "vpc-0deb766aa06396f05",
    "cidr_block": "172.17.128.0/20",
    "availability_zone": "us-east-1a",
    "map_public_ip": false,
    "tags": {
      "Name": "Terra-Auto-subnet-private1-us-east-1a"
    }
  },
  "subnet-087d5dbe8a831fe19": {
    "vpc_id": "vpc-0deb766aa06396f05",
    "cidr_block": "172.17.0.0/20",
    "availability_zone": "us-east-1a",
    "map_public_ip": false,
    "tags": {
      "Name": "Terra-Auto-subnet-public1-us-east-1a"
    }
  }
}

igw_configs = {
  "igw-09f35f6915b6e9858": {
    "vpc_id": "vpc-0deb766aa06396f05",
    "tags": {
      "Name": "Terra-Auto-igw"
    }
  }
}

nat_configs = {
  "nat-05f2e1863c554a238": {
    "subnet_id": "subnet-087d5dbe8a831fe19",
    "tags": {
      "Name": "Terra-Auto-nat-public1-us-east-1a"
    }
  }
}

sg_configs = {
  "sg-040187bddedb38808": {
    "name": "default",
    "description": "default VPC security group",
    "vpc_id": "vpc-0deb766aa06396f05",
    "ingress": [
      {
        "from_port": 0,
        "to_port": 0,
        "protocol": "-1",
        "cidr_blocks": [
          "0.0.0.0/0"
        ]
      }
    ],
    "egress": [
      {
        "from_port": 0,
        "to_port": 0,
        "protocol": "-1",
        "cidr_blocks": [
          "0.0.0.0/0"
        ]
      }
    ],
    "tags": {}
  }
}

rt_configs = {
  "rtb-048d0996dc22e54cb": {
    "vpc_id": "vpc-0deb766aa06396f05",
    "routes": [
      {
        "destination_cidr_block": "172.17.0.0/16",
        "gateway_id": "local"
      },
      {
        "destination_cidr_block": "0.0.0.0/0",
        "gateway_id": "igw-09f35f6915b6e9858"
      }
    ],
    "tags": {
      "Name": "Terra-Auto-rtb-public"
    }
  },
  "rtb-0f9b0c42f45d5da6f": {
    "vpc_id": "vpc-0deb766aa06396f05",
    "routes": [
      {
        "destination_cidr_block": "172.17.0.0/16",
        "gateway_id": "local"
      }
    ],
    "tags": {}
  },
  "rtb-0f4737b749a439b17": {
    "vpc_id": "vpc-0deb766aa06396f05",
    "routes": [
      {
        "destination_cidr_block": "172.17.0.0/16",
        "gateway_id": "local"
      },
      {
        "destination_cidr_block": "0.0.0.0/0",
        "gateway_id": "nat-05f2e1863c554a238"
      }
    ],
    "tags": {
      "Name": "Terra-Auto-rtb-private1-us-east-1a"
    }
  }
}
