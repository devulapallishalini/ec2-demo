# Remote state in S3 with DynamoDB locking. Create both first with ../bootstrap.
# Backend settings can't use variables, so the names are written out here.
#
# The dev workspace uses its own state file:
#   s3://tf-state-949926374215-ap-south-1/env:/dev/ec2-demo/terraform.tfstate

terraform {
  backend "s3" {
    bucket         = "tf-state-949926374215-ap-south-1"
    key            = "ec2-demo/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
