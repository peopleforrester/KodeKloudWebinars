# ABOUTME: traffic-generator Lambda + IAM (S3 read on test data + CloudWatch Logs).
# ABOUTME: Drives synthetic UCI Adult traffic at the shadow-mirror over HTTPS.
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

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  function_name = "traffic-generator-${var.attendee_id}"
}

data "aws_iam_policy_document" "assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "this" {
  name               = "${local.function_name}-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
  tags               = var.tags
}

# The generator only reads the test-data objects from S3; it reaches the
# shadow-mirror over HTTPS, which needs no IAM.
data "aws_iam_policy_document" "policy" {
  statement {
    sid    = "ReadTestData"
    effect = "Allow"
    actions = [
      "s3:GetObject",
    ]
    resources = ["${var.shadow_logs_bucket_arn}/*"]
  }
  statement {
    sid    = "Logs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${local.function_name}:*"]
  }
}

resource "aws_iam_role_policy" "this" {
  name   = "traffic-generator"
  role   = aws_iam_role.this.id
  policy = data.aws_iam_policy_document.policy.json
}

# Lab simplifications, documented inline: no VPC, AES256 (not KMS CMK) env vars,
# no reserved concurrency, no code signing, no DLQ (manual invocation returns a
# summary directly). X-Ray tracing IS enabled (genuine control).
#tfsec:ignore:aws-lambda-enable-tracing
resource "aws_lambda_function" "this" {
  #checkov:skip=CKV_AWS_117:Lambda intentionally not in a VPC for this self-contained lab.
  #checkov:skip=CKV_AWS_173:Env vars use AES256 (no KMS CMK) as a lab simplification.
  #checkov:skip=CKV_AWS_115:No reserved concurrency in the single-attendee lab.
  #checkov:skip=CKV_AWS_272:Code signing is out of scope for the lab.
  #checkov:skip=CKV_AWS_116:DLQ omitted; manual invocation returns a summary synchronously.
  function_name    = local.function_name
  role             = aws_iam_role.this.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = var.filename
  source_code_hash = var.source_code_hash
  timeout          = 300
  memory_size      = 512
  tags             = var.tags

  tracing_config {
    mode = "Active"
  }

  environment {
    variables = {
      SHADOW_MIRROR_URL       = var.shadow_mirror_url
      TEST_DATA_URI           = var.test_data_uri
      DISAGREEMENT_REGION_URI = var.disagreement_region_uri
    }
  }
}
