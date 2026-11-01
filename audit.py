"""Fail unless the booking app responds with HTTP 200 and EC2 is running."""

import argparse
import os
import sys
from urllib.error import URLError
from urllib.request import urlopen

import boto3
from botocore.exceptions import BotoCoreError, ClientError


def parse_args():
    parser = argparse.ArgumentParser(description="Check booking app and EC2 health.")
    parser.add_argument("--url", default=os.environ.get("APP_URL"))
    parser.add_argument(
        "--instance-id",
        default=os.environ.get("EC2_INSTANCE_ID"),
    )
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", "ap-south-1"))
    return parser.parse_args()


def check_http(url):
    with urlopen(url, timeout=15) as response:
        if response.status != 200:
            raise RuntimeError(f"App endpoint returned HTTP {response.status}, expected 200")
    print(f"HTTP health check passed: {url}")


def check_instance(instance_id, region):
    ec2 = boto3.client("ec2", region_name=region)
    if instance_id:
        response = ec2.describe_instances(InstanceIds=[instance_id])
    else:
        response = ec2.describe_instances(
            Filters=[
                {"Name": "tag:Name", "Values": ["demo-dev-web"]},
                {
                    "Name": "instance-state-name",
                    "Values": ["pending", "running", "stopping", "stopped"],
                },
            ]
        )
    instances = [
        instance
        for reservation in response["Reservations"]
        for instance in reservation["Instances"]
    ]
    if len(instances) != 1:
        target = instance_id or "the instance tagged Name=demo-dev-web"
        raise RuntimeError(f"Expected one EC2 instance for {target}, found {len(instances)}")

    instance = instances[0]
    instance_id = instance["InstanceId"]
    state = instance["State"]["Name"]
    if state != "running":
        raise RuntimeError(f"EC2 instance {instance_id} is {state}, expected running")
    print(f"EC2 health check passed: {instance_id} is running in {region}")
    return instance


def main():
    args = parse_args()
    try:
        instance = check_instance(args.instance_id, args.region)
    except (
        BotoCoreError,
        ClientError,
        RuntimeError,
        ValueError,
    ) as error:
        print(f"ERROR: EC2 health check failed: {error}", file=sys.stderr)
        return 1

    url = args.url or (
        f"http://{instance['PublicIpAddress']}"
        if instance.get("PublicIpAddress")
        else None
    )
    if not url:
        print("ERROR: HTTP health check failed: no app URL or public IP available", file=sys.stderr)
        return 1

    try:
        check_http(url)
    except (URLError, RuntimeError, TimeoutError, ValueError) as error:
        print(f"ERROR: HTTP health check failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
