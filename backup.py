"""Create a compressed archive of booking app data and upload it to S3."""

import logging
import os
import shlex
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError


LOG = logging.getLogger("booking-backup")
DEFAULT_BACKUP_PATHS = (
    "/usr/share/nginx/html",
    "/var/lib/booking-app",
    "/etc/nginx",
    "/var/log/nginx",
    "/etc/prometheus",
    "/etc/grafana/provisioning",
    "/opt/booking-monitor",
)


def backup_paths():
    configured = os.environ.get("BACKUP_PATHS")
    values = shlex.split(configured) if configured else DEFAULT_BACKUP_PATHS
    paths = []
    for value in values:
        path = Path(value)
        if path.exists():
            paths.append(path)
        else:
            LOG.warning("Skipping missing backup path: %s", path)
    if not paths:
        raise ValueError("No backup paths exist; check BACKUP_PATHS")
    return paths


def create_archive(paths, archive_path):
    with tarfile.open(archive_path, "w:gz") as archive:
        for path in paths:
            archive.add(path, arcname=path.as_posix().lstrip("/"))


def main():
    bucket = os.environ.get("BACKUP_BUCKET")
    region = os.environ.get("AWS_DEFAULT_REGION")
    if not bucket or not region:
        LOG.error("BACKUP_BUCKET and AWS_DEFAULT_REGION must be configured")
        return 2

    try:
        paths = backup_paths()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / f"booking-backup-{timestamp}.tar.gz"
            create_archive(paths, archive_path)

            key = f"backups/booking-backup-{timestamp}.tar.gz"
            client = boto3.client("s3", region_name=region)
            client.upload_file(
                str(archive_path),
                bucket,
                key,
                ExtraArgs={"ServerSideEncryption": "AES256"},
            )
        LOG.info("Uploaded s3://%s/%s", bucket, key)
        return 0
    except (BotoCoreError, ClientError, OSError, tarfile.TarError, ValueError):
        LOG.exception("Backup failed")
        return 1


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    sys.exit(main())
