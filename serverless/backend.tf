terraform {
  backend "s3" {
    bucket         = "tf-state-949926374215-ap-south-1"
    key            = "cloud-ops-app/serverless/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
