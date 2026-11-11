# Serverless API

This stack deploys a Python 3.12 Lambda behind an API Gateway HTTP API. The
application is in `src/app.py`; `archive_file` packages it, and Terraform
uploads a versioned archive to a private S3 bucket before configuring Lambda.
The deployment key is based on source-file contents rather than ZIP metadata,
so checkout timestamps do not trigger unnecessary artifact replacements.
Lambda can write logs only to its own 14-day CloudWatch log group.

The `serverless/` directory has a separate Terraform state from the existing
EC2 project. Its S3 backend uses the project's existing state bucket and lock
table, with a separate state key. Do not initialize this stack with local state
for an AWS deployment.

## Deploy locally

Prerequisites: Terraform 1.16.4, Python 3.12, AWS credentials authorized to
manage the resources in `main.tf`, and access to the configured remote-state
bucket and DynamoDB lock table.

```powershell
$env:PYTHONPATH = "serverless\src"
python -m unittest discover -s serverless\tests -v
terraform -chdir=serverless init
terraform -chdir=serverless plan
terraform -chdir=serverless apply
terraform -chdir=serverless output -raw invoke_url
```

## Verify the live API

After apply, use the URL from `terraform output -raw invoke_url`:

```powershell
$url = terraform -chdir=serverless output -raw invoke_url
curl.exe "$url/"
curl.exe "$url/health"
```

Both routes return JSON with a message, method, path, request ID, and current
UTC timestamp. Capture the terminal or browser response as deployment proof;
the URL cannot be supplied until the stack has been applied in an AWS account.

## GitHub Actions

Pull requests run the handler tests and Terraform formatting/validation. A push
to `main` applies this stack after checks pass. Configure the `dev` GitHub
environment and its `AWS_ROLE_TO_ASSUME` secret with an IAM role ARN trusted by
GitHub Actions OIDC. The role needs permission to use the configured remote
state bucket and lock table and to manage the Lambda, API Gateway, S3, IAM, and
CloudWatch resources in this stack. The workflow summary prints the invoke and
health URLs after a successful apply.
