import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import audit


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class AuditTests(unittest.TestCase):
    @patch.object(audit, "urlopen", return_value=FakeResponse())
    def test_http_check_accepts_only_status_200(self, urlopen):
        audit.check_http("http://example.test/")
        urlopen.assert_called_once_with("http://example.test/", timeout=15)

    @patch.object(
        audit,
        "urlopen",
        side_effect=HTTPError("http://example.test/", 503, "Unavailable", {}, None),
    )
    def test_http_check_rejects_non_200_status(self, _urlopen):
        with self.assertRaises(HTTPError):
            audit.check_http("http://example.test/")

    @patch.object(audit.boto3, "client")
    def test_instance_check_requires_running_state(self, client):
        instance = {
            "InstanceId": "i-1234567890abcdef0",
            "State": {"Name": "running"},
            "PublicIpAddress": "203.0.113.1",
        }
        client.return_value.describe_instances.return_value = {
            "Reservations": [{"Instances": [instance]}]
        }
        self.assertEqual(
            audit.check_instance("i-1234567890abcdef0", "ap-south-1"),
            instance,
        )
        client.assert_called_once_with("ec2", region_name="ap-south-1")

    @patch.object(audit.boto3, "client")
    def test_instance_check_discovers_instance_by_name_tag(self, client):
        instance = {
            "InstanceId": "i-1234567890abcdef0",
            "State": {"Name": "running"},
            "PublicIpAddress": "203.0.113.1",
        }
        client.return_value.describe_instances.return_value = {
            "Reservations": [{"Instances": [instance]}]
        }

        self.assertEqual(audit.check_instance(None, "ap-south-1"), instance)
        client.return_value.describe_instances.assert_called_once_with(
            Filters=[
                {"Name": "tag:Name", "Values": ["demo-dev-web"]},
                {
                    "Name": "instance-state-name",
                    "Values": ["pending", "running", "stopping", "stopped"],
                },
            ]
        )

    @patch.object(audit.boto3, "client")
    def test_instance_check_rejects_non_running_state(self, client):
        client.return_value.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "State": {"Name": "stopped"},
                        }
                    ]
                }
            ]
        }
        with self.assertRaisesRegex(RuntimeError, "is stopped"):
            audit.check_instance("i-1234567890abcdef0", "ap-south-1")

    @patch.object(audit.boto3, "client")
    def test_instance_check_rejects_ambiguous_discovery(self, client):
        client.return_value.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {"InstanceId": "i-one", "State": {"Name": "running"}},
                        {"InstanceId": "i-two", "State": {"Name": "running"}},
                    ]
                }
            ]
        }

        with self.assertRaisesRegex(RuntimeError, "found 2"):
            audit.check_instance(None, "ap-south-1")


if __name__ == "__main__":
    unittest.main()
