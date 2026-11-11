variable "region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Project name used in resource names"
  type        = string
  default     = "cloud-ops-app"
}

variable "environment" {
  description = "Environment name; this stack is limited to dev to reduce costs"
  type        = string
  default     = "dev"

  validation {
    condition     = var.environment == "dev"
    error_message = "Only the dev environment is enabled to limit costs."
  }
}

locals {
  name_prefix = "${var.project}-${var.environment}"
}
