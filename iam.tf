resource "aws_iam_role" "web_backup" {
  name = "${local.name_prefix}-web-backup"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "web_backup" {
  name = "${local.name_prefix}-s3-backup"
  role = aws_iam_role.web_backup.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucketMultipartUploads"
        ]
        Resource = aws_s3_bucket.backups.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:AbortMultipartUpload",
          "s3:ListMultipartUploadParts",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.backups.arn}/*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "web" {
  name = "${local.name_prefix}-web"
  role = aws_iam_role.web_backup.name
}
