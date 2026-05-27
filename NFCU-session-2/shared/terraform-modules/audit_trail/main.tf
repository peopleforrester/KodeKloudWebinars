# ABOUTME: Shared audit-trail S3 bucket for promotion/rollback evidence.
# ABOUTME: Reused by Session 2 and (planned) Session 3; versioned and encrypted.
# SPDX-License-Identifier: Apache-2.0

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Access logging is omitted as a documented lab simplification (it would require
# a second, equally locked-down log bucket).
#tfsec:ignore:aws-s3-enable-bucket-logging
resource "aws_s3_bucket" "audit" {
  #checkov:skip=CKV_AWS_18:Access logging omitted as a documented lab simplification.
  #checkov:skip=CKV_AWS_144:Cross-region replication is out of scope for the lab.
  #checkov:skip=CKV_AWS_145:SSE-S3 (AES256) is used instead of a KMS CMK in the lab.
  #checkov:skip=CKV2_AWS_61:Lifecycle config omitted; audit entries are retained.
  #checkov:skip=CKV2_AWS_62:Event notifications are out of scope for the lab.
  bucket = "workshop-lab-${var.attendee_id}-audit"

  # Production would additionally enable MFA-delete and S3 Object Lock for
  # tamper-evidence. Both are intentionally omitted here and documented in
  # this module's README as lab-vs-production gaps.
  tags = var.tags
}

resource "aws_s3_bucket_versioning" "audit" {
  bucket = aws_s3_bucket.audit.id
  versioning_configuration {
    status = "Enabled"
  }
}

# The lab uses SSE-S3 (AES256) rather than a customer-managed KMS key to keep the
# sandbox self-contained; production would use a CMK with a key policy.
#tfsec:ignore:aws-s3-encryption-customer-key
resource "aws_s3_bucket_server_side_encryption_configuration" "audit" {
  bucket = aws_s3_bucket.audit.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "audit" {
  bucket                  = aws_s3_bucket.audit.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
