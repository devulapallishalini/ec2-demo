import os
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import backup


class BackupTests(unittest.TestCase):
    def test_create_archive_includes_configured_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "app"
            source.mkdir()
            (source / "index.html").write_text("booking app")
            archive_path = Path(temp_dir) / "backup.tar.gz"

            backup.create_archive([source], archive_path)

            with tarfile.open(archive_path, "r:gz") as archive_file:
                names = archive_file.getnames()
                self.assertEqual(len(names), 2)
                self.assertTrue(names[0].endswith("/app"))
                self.assertTrue(names[1].endswith("/app/index.html"))
                self.assertEqual(
                    archive_file.extractfile(names[1]).read(),
                    b"booking app",
                )

    @patch.object(backup.boto3, "client")
    def test_main_uploads_encrypted_archive(self, client):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "app"
            source.mkdir()
            (source / "index.html").write_text("booking app")
            environment = {
                "BACKUP_BUCKET": "booking-backups",
                "AWS_DEFAULT_REGION": "ap-south-1",
                "BACKUP_PATHS": str(source).replace("\\", "/"),
            }
            with patch.dict(os.environ, environment):
                self.assertEqual(backup.main(), 0)

        client.assert_called_once_with("s3", region_name="ap-south-1")
        upload = client.return_value.upload_file.call_args
        self.assertEqual(upload.args[1], "booking-backups")
        self.assertTrue(upload.args[2].startswith("backups/booking-backup-"))
        self.assertEqual(upload.kwargs["ExtraArgs"], {"ServerSideEncryption": "AES256"})


if __name__ == "__main__":
    unittest.main()
