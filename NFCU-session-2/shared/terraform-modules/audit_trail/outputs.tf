# ABOUTME: Outputs for the shared audit_trail module.
# ABOUTME: Exposes the audit bucket name and ARN to composing configurations.
# SPDX-License-Identifier: Apache-2.0

output "bucket_name" {
  description = "Name of the audit S3 bucket."
  value       = aws_s3_bucket.audit.id
}

output "bucket_arn" {
  description = "ARN of the audit S3 bucket."
  value       = aws_s3_bucket.audit.arn
}
