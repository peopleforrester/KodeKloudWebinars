# ABOUTME: comparison Lambda + IAM + 5-minute EventBridge schedule + DLQ.
# ABOUTME: Joins shadow logs, emits CloudWatch metrics, writes comparison results.
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
  function_name = "comparison-${var.attendee_id}"
}

# The dead-letter queue captures failed asynchronous comparison invocations.
# SSE-SQS (AES256) is used rather than a KMS CMK as a documented lab
# simplification.
#tfsec:ignore:aws-sqs-enable-queue-encryption
resource "aws_sqs_queue" "dlq" {
  #checkov:skip=CKV_AWS_27:SSE-SQS (AES256) used instead of a KMS CMK in the lab.
  name                      = "${local.function_name}-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true
  tags                      = var.tags
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

data "aws_iam_policy_document" "policy" {
  statement {
    sid    = "ReadShadowLogs"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      var.shadow_logs_bucket_arn,
      "${var.shadow_logs_bucket_arn}/*",
    ]
  }
  statement {
    sid    = "ReadWriteResults"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
    ]
    resources = [
      var.comparison_results_bucket_arn,
      "${var.comparison_results_bucket_arn}/*",
    ]
  }
  statement {
    sid    = "EmitMetrics"
    effect = "Allow"
    actions = [
      "cloudwatch:PutMetricData",
    ]
    resources = ["*"]
  }
  statement {
    sid    = "DeadLetter"
    effect = "Allow"
    actions = [
      "sqs:SendMessage",
    ]
    resources = [aws_sqs_queue.dlq.arn]
  }
  statement {
    sid    = "Logs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:${var.aws_region}:${var.account_id}:log-group:/aws/lambda/${local.function_name}:*"]
  }
}

resource "aws_iam_role_policy" "this" {
  name   = "comparison"
  role   = aws_iam_role.this.id
  policy = data.aws_iam_policy_document.policy.json
}

# Lab simplifications, documented inline: no VPC, AES256 (not KMS CMK) env vars,
# no reserved concurrency, no code signing. A dead-letter queue and X-Ray
# tracing ARE configured (genuine controls).
#tfsec:ignore:aws-lambda-enable-tracing
resource "aws_lambda_function" "this" {
  #checkov:skip=CKV_AWS_117:Lambda intentionally not in a VPC for this self-contained lab.
  #checkov:skip=CKV_AWS_173:Env vars use AES256 (no KMS CMK) as a lab simplification.
  #checkov:skip=CKV_AWS_115:No reserved concurrency in the single-attendee lab.
  #checkov:skip=CKV_AWS_272:Code signing is out of scope for the lab.
  function_name    = local.function_name
  role             = aws_iam_role.this.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = var.filename
  source_code_hash = var.source_code_hash
  timeout          = 120
  memory_size      = 256
  tags             = var.tags

  tracing_config {
    mode = "Active"
  }

  dead_letter_config {
    target_arn = aws_sqs_queue.dlq.arn
  }

  environment {
    variables = {
      SHADOW_LOG_BUCKET         = var.shadow_logs_bucket
      COMPARISON_RESULTS_BUCKET = var.comparison_results_bucket
      PROMOTION_CRITERIA_PATH   = var.promotion_criteria_path
    }
  }
}

resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "${local.function_name}-schedule"
  schedule_expression = "rate(5 minutes)"
  tags                = var.tags
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.schedule.name
  target_id = "comparison-lambda"
  arn       = aws_lambda_function.this.arn
}

resource "aws_lambda_permission" "events" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule.arn
}
