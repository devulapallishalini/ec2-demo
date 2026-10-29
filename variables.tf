# All inputs live here. Set them in dev.tfvars.

variable "region" {
  description = "AWS region to deploy into"
  type        = string
}

variable "project" {
  description = "Project name, used in resource names"
  type        = string
  default     = "demo"
}

variable "environment" {
  description = "Environment name; this project is limited to dev to reduce costs"
  type        = string

  validation {
    condition     = var.environment == "dev"
    error_message = "Only the dev environment is enabled to limit costs."
  }
}

# --- Network ---

variable "vpc_cidr" {
  description = "Address range for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Address range for the public subnet (must sit inside vpc_cidr)"
  type        = string
  default     = "10.0.1.0/24"
}

variable "my_ip_cidr" {
  description = "Your public IP allowed to SSH and access Grafana, e.g. 203.0.113.10/32"
  type        = string
  # No default on purpose: SSH should never be open to the whole internet by accident.
}

# --- Server ---

variable "instance_type" {
  description = "EC2 size; restricted to t3.micro to limit costs"
  type        = string
  default     = "t3.micro"

  validation {
    condition     = var.instance_type == "t3.micro"
    error_message = "instance_type must be t3.micro to limit costs."
  }
}

variable "ami_name_pattern" {
  description = "Image tag: AMI name pattern; the newest Amazon-owned match is used"
  type        = string
  default     = "al2023-ami-2023.*-x86_64"
}

variable "public_key_path" {
  description = "Public SSH key to install on the instance (relative to this folder, so CI can find it)"
  type        = string
  default     = "keys/deployer.pub"
}

locals {
  name_prefix = "${var.project}-${var.environment}"
}
