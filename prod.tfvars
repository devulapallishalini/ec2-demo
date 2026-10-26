environment = "prod"
region      = "ap-south-1"

vpc_cidr           = "10.1.0.0/16"
public_subnet_cidr = "10.1.1.0/24"
my_ip_cidr         = "219.91.183.38/32"

instance_type    = "t3.small"
ami_name_pattern = "al2023-ami-2023.*-x86_64"
