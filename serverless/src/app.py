import json
from datetime import datetime, timezone
from typing import Any


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    request_context = event.get("requestContext") or {}
    http_context = request_context.get("http") or {}
    path = event.get("rawPath") or event.get("path") or "/"
    method = http_context.get("method") or event.get("httpMethod") or "GET"

    if path not in ("/", "/health"):
        status_code = 404
        payload = {"error": "Not found"}
    elif method != "GET":
        status_code = 405
        payload = {"error": "Method not allowed"}
    else:
        payload = {
            "message": "Hello from AWS Lambda!",
            "method": method,
            "path": path,
            "request_id": request_context.get("requestId")
            or getattr(context, "aws_request_id", None),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        status_code = 200

    return {
        "statusCode": status_code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(payload),
    }
