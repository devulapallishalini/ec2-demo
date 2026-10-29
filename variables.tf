# All inputs live here. Set them per environment in dev.tfvars / prod.tfvars.

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
  description = "Environment name, e.g. dev or prod"
  type        = string

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment must be \"dev\" or \"prod\"."
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
  description = "EC2 size"
  type        = string
  default     = "t3.micro"
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
