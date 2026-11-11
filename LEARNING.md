# Serverless learning log

## What this project adds

- Replaced the need for an always-on API server with a Python 3.12 Lambda
  function invoked through an API Gateway HTTP API.
- Used Terraform's `archive_file` data source to package the handler and
  uploaded the ZIP to a private, versioned S3 deployment bucket.
- Kept deployment infrastructure separate from the existing EC2 stack and
  isolated its Terraform state key.
- Scoped the Lambda execution role to writing logs to its own CloudWatch log
  group, with 14-day retention.
- Added handler tests and a GitHub Actions workflow that validates pull
  requests and applies the serverless stack on pushes to `main`.

## Functional check

Run the handler tests locally:

```powershell
$env:PYTHONPATH = "serverless\src"
python -m unittest discover -s serverless\tests -v
```

After deployment, obtain the live API Gateway URL and check both routes:

```powershell
$url = terraform -chdir=serverless output -raw invoke_url
curl.exe "$url/"
curl.exe "$url/health"
```

## Deployment proof

No AWS deployment has been run from this workspace, so there is no verified
invoke URL or live-response screenshot to report yet. After the GitHub Actions
apply succeeds, the workflow summary and `terraform output -raw invoke_url`
provide the URL. Save a screenshot of a successful `curl.exe` response or
browser response as the live functional verification.
