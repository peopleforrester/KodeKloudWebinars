# ABOUTME: Two S3 buckets for shadow logs and comparison results.
# ABOUTME: Versioned, AES256-encrypted, public-access-blocked, 30-day expiry.
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

locals {
  buckets = {
    shadow_logs        = "workshop-lab-${var.attendee_id}-shadow-logs"
    comparison_results = "workshop-lab-${var.attendee_id}-comparison-results"
  }
}

# Access logging, cross-region replication, and event notifications are omitted
# as documented lab simplifications (each would require additional locked-down
# infrastructure beyond the scope of a single-attendee teaching lab).
#tfsec:ignore:aws-s3-enable-bucket-logging
resource "aws_s3_bucket" "this" {
  #checkov:skip=CKV_AWS_18:Access logging omitted as a documented lab simplification.
  #checkov:skip=CKV_AWS_144:Cross-region replication is out of scope for the lab.
  #checkov:skip=CKV_AWS_145:SSE-S3 (AES256) is used instead of a KMS CMK in the lab.
  #checkov:skip=CKV2_AWS_62:Event notifications are out of scope for the lab.
  for_each = local.buckets

  bucket = each.value
  tags   = var.tags
}

resource "aws_s3_bucket_versioning" "this" {
  for_each = aws_s3_bucket.this

  bucket = each.value.id
  versioning_configuration {
    status = "Enabled"
  }
}

# SSE-S3 (AES256) is used instead of a customer-managed KMS key to keep the
# sandbox self-contained; production would use a CMK with a key policy.
#tfsec:ignore:aws-s3-encryption-customer-key
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  for_each = aws_s3_bucket.this

  bucket = each.value.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  for_each = aws_s3_bucket.this

  bucket                  = each.value.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  for_each = aws_s3_bucket.this

  bucket = each.value.id

  rule {
    id     = "expire-after-30-days"
    status = "Enabled"

    filter {}

    expiration {
      days = 30
    }

    # Clean up failed multipart uploads so they do not accrue silent cost.
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}
