aws_region = "us-east-1"

vpc_configs = {
  "vpc-0deb766aa06396f05": {
    "cidr_block": "172.17.0.0/16",
    "tags": {
      "Name": "Terra-Auto-vpc"
    },
    "enable_dns_support": true,
    "enable_dns_hostnames": true
  },
  "vpc-0ac3883de5bde45b6": {
    "cidr_block": "172.31.0.0/16",
    "tags": {
      "Name": "Default_VPC"
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
  },
  "subnet-05716b00f5ce2ae37": {
    "vpc_id": "vpc-0ac3883de5bde45b6",
    "cidr_block": "172.31.64.0/20",
    "availability_zone": "us-east-1f",
    "map_public_ip": true,
    "tags": {
      "Name": "Sub_us-east-1f"
    }
  },
  "subnet-037ca5150d86bfa9c": {
    "vpc_id": "vpc-0ac3883de5bde45b6",
    "cidr_block": "172.31.80.0/20",
    "availability_zone": "us-east-1a",
    "map_public_ip": true,
    "tags": {
      "Name": "Sub_us-east-1a"
    }
  },
  "subnet-0d3170b8337358f5c": {
    "vpc_id": "vpc-0ac3883de5bde45b6",
    "cidr_block": "172.31.48.0/20",
    "availability_zone": "us-east-1e",
    "map_public_ip": true,
    "tags": {
      "Name": "Sub_us-east-1e"
    }
  },
  "subnet-0b8c870cd8cf2b6e8": {
    "vpc_id": "vpc-0ac3883de5bde45b6",
    "cidr_block": "172.31.16.0/20",
    "availability_zone": "us-east-1b",
    "map_public_ip": true,
    "tags": {
      "Name": "Sub_us-east-1b"
    }
  },
  "subnet-025fcd0dc02a182c1": {
    "vpc_id": "vpc-0ac3883de5bde45b6",
    "cidr_block": "172.31.32.0/20",
    "availability_zone": "us-east-1c",
    "map_public_ip": true,
    "tags": {
      "Name": "Sub_us-east-1c"
    }
  },
  "subnet-01a1b0471903cf7ca": {
    "vpc_id": "vpc-0ac3883de5bde45b6",
    "cidr_block": "172.31.0.0/20",
    "availability_zone": "us-east-1d",
    "map_public_ip": true,
    "tags": {
      "Name": "Sub_us-east-1d"
    }
  }
}

igw_configs = {
  "igw-09f35f6915b6e9858": {
    "vpc_id": "vpc-0deb766aa06396f05",
    "tags": {
      "Name": "Terra-Auto-igw"
    }
  },
  "igw-0759257f25ef27e69": {
    "vpc_id": "vpc-0ac3883de5bde45b6",
    "tags": {}
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
  },
  "sg-0a2929bc0cc568a1f": {
    "name": "default",
    "description": "default VPC security group",
    "vpc_id": "vpc-0ac3883de5bde45b6",
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
  },
  "rtb-0cf454d4d34bae4bb": {
    "vpc_id": "vpc-0ac3883de5bde45b6",
    "routes": [
      {
        "destination_cidr_block": "172.31.0.0/16",
        "gateway_id": "local"
      },
      {
        "destination_cidr_block": "0.0.0.0/0",
        "gateway_id": "igw-0759257f25ef27e69"
      }
    ],
    "tags": {}
  }
}
