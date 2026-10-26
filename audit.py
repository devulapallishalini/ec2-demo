"""List every EC2 instance in the account and warn about long-running ones.

Checks all regions enabled for the account. For each instance it prints the
region, ID, Name tag, state, type and launch time, and prints a WARNING for
any instance that has been running longer than the threshold (24h default).

Usage:
    python audit.py                    # all regions, 24h threshold
    python audit.py --hours 12         # custom threshold
    python audit.py --region ap-south-1
    python audit.py --fail-on-warning  # exit 1 if anything is flagged (for CI)

Credentials come from the usual AWS sources (aws configure, env vars, IAM role).
Needs ec2:DescribeRegions and ec2:DescribeInstances.
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError


def enabled_regions(session):
    ec2 = session.client("ec2", region_name="us-east-1")
    regions = ec2.describe_regions(AllRegions=False)["Regions"]
    return sorted(r["RegionName"] for r in regions)


def instances_in_region(session, region):
    ec2 = session.client("ec2", region_name=region)
    paginator = ec2.get_paginator("describe_instances")
    for page in paginator.paginate():
        for reservation in page["Reservations"]:
            for inst in reservation["Instances"]:
                tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
                yield {
                    "region": region,
                    "id": inst["InstanceId"],
                    "name": tags.get("Name", "-"),
                    "state": inst["State"]["Name"],
                    "type": inst["InstanceType"],
                    "launch_time": inst["LaunchTime"],  # timezone-aware UTC
                }


def format_age(delta):
    hours = int(delta.total_seconds() // 3600)
    days, hours = divmod(hours, 24)
    return f"{days}d {hours}h" if days else f"{hours}h"


def main():
    parser = argparse.ArgumentParser(description="Audit EC2 instances.")
    parser.add_argument("--hours", type=float, default=24,
                        help="warn when running longer than this (default 24)")
    parser.add_argument("--region", help="only check this region")
    parser.add_argument("--fail-on-warning", action="store_true",
                        help="exit with code 1 if any instance is flagged")
    args = parser.parse_args()

    session = boto3.Session()
    now = datetime.now(timezone.utc)
    threshold = timedelta(hours=args.hours)

    try:
        regions = [args.region] if args.region else enabled_regions(session)
    except (BotoCoreError, ClientError) as e:
        print(f"ERROR: could not list regions: {e}", file=sys.stderr)
        return 2

    rows, warnings, errors = [], [], []
    for region in regions:
        try:
            rows.extend(instances_in_region(session, region))
        except (BotoCoreError, ClientError) as e:
            errors.append(f"{region}: {e}")

    print(f"EC2 audit at {now:%Y-%m-%d %H:%M UTC} "
          f"({len(regions)} region(s), threshold {args.hours:g}h)\n")

    if rows:
        header = f"{'REGION':<15} {'INSTANCE ID':<20} {'NAME':<24} {'STATE':<12} {'TYPE':<12} LAUNCHED (UTC)"
        print(header)
        print("-" * len(header))
        for r in sorted(rows, key=lambda r: (r["region"], r["launch_time"])):
            print(f"{r['region']:<15} {r['id']:<20} {r['name'][:24]:<24} "
                  f"{r['state']:<12} {r['type']:<12} {r['launch_time']:%Y-%m-%d %H:%M}")
            age = now - r["launch_time"]
            if r["state"] == "running" and age > threshold:
                warnings.append(
                    f"WARNING: {r['id']} ({r['name']}, {r['type']}) in {r['region']} "
                    f"has been running for {format_age(age)}"
                )
    else:
        print("No EC2 instances found.")

    print(f"\n{len(rows)} instance(s), {len(warnings)} warning(s)")
    for w in warnings:
        print(w)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        return 2
    if warnings and args.fail_on_warning:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
