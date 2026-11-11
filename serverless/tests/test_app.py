import json
import unittest
from unittest.mock import Mock

from app import lambda_handler


class LambdaHandlerTests(unittest.TestCase):
    def test_root_returns_dynamic_json_response(self):
        context = Mock(aws_request_id="request-123")
        response = lambda_handler(
            {
                "rawPath": "/",
                "requestContext": {"http": {"method": "GET"}},
            },
            context,
        )

        payload = json.loads(response["body"])
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["headers"]["content-type"], "application/json")
        self.assertEqual(payload["message"], "Hello from AWS Lambda!")
        self.assertEqual(payload["path"], "/")
        self.assertEqual(payload["request_id"], "request-123")
        self.assertTrue(payload["timestamp"])

    def test_health_route_uses_gateway_request_id(self):
        response = lambda_handler(
            {
                "rawPath": "/health",
                "requestContext": {
                    "requestId": "gateway-456",
                    "http": {"method": "GET"},
                },
            },
            Mock(),
        )

        payload = json.loads(response["body"])
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(payload["request_id"], "gateway-456")
        self.assertEqual(payload["path"], "/health")

    def test_unknown_path_returns_not_found(self):
        response = lambda_handler(
            {"rawPath": "/missing", "requestContext": {"http": {"method": "GET"}}},
            Mock(),
        )

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(json.loads(response["body"]), {"error": "Not found"})

    def test_non_get_request_returns_method_not_allowed(self):
        response = lambda_handler(
            {"rawPath": "/", "requestContext": {"http": {"method": "POST"}}},
            Mock(),
        )

        self.assertEqual(response["statusCode"], 405)
        self.assertEqual(
            json.loads(response["body"]),
            {"error": "Method not allowed"},
        )


if __name__ == "__main__":
    unittest.main()
