output "invoke_url" {
  description = "Base URL for the deployed HTTP API"
  value       = aws_apigatewayv2_api.http.api_endpoint
}

output "health_url" {
  description = "Health-check endpoint for the deployed HTTP API"
  value       = "${aws_apigatewayv2_api.http.api_endpoint}/health"
}

output "deployment_bucket" {
  description = "Private S3 bucket holding versioned Lambda deployment archives"
  value       = aws_s3_bucket.deployments.bucket
}
