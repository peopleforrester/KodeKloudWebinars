# ABOUTME: Per-attendee NFCU Session 3 infra: buckets, IAM, five Lambdas, schedule.
# ABOUTME: One Terraform workspace per attendee. drift-detector runs every 2 min.

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.4"
    }
  }
}

provider "aws" {
  region = var.region
}

data "aws_caller_identity" "current" {}

locals {
  prefix             = "workshop-lab-${var.attendee_id}"
  baseline_bucket    = "${local.prefix}-baseline"
  drift_reports_buck = "${local.prefix}-drift-reports"
  shadow_logs_bucket = var.shadow_logs_bucket != "" ? var.shadow_logs_bucket : "${local.prefix}-shadow-logs"
  endpoint_name      = var.endpoint_name != "" ? var.endpoint_name : "${local.prefix}-production"
  drift_alarm_name   = "Drift-PSI-${var.attendee_id}"
  zip_lambdas        = ["drift-detector", "drift-simulator", "incident-simulator"]
  common_tags = {
    Project    = "nfcu-session-3"
    Session    = "monitoring"
    AttendeeId = var.attendee_id
    ManagedBy  = "terraform"
  }
}

# ---------------------------------------------------------------------------
# S3 buckets (two per attendee, per task 7.3). Shadow-logs is read-only input
# created by the S1/2 data-capture path and is treated as external.
# ---------------------------------------------------------------------------
resource "aws_s3_bucket" "baseline" {
  bucket = local.baseline_bucket
  tags   = local.common_tags
}

resource "aws_s3_bucket" "drift_reports" {
  bucket = local.drift_reports_buck
  tags   = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "baseline" {
  bucket                  = aws_s3_bucket.baseline.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "drift_reports" {
  bucket                  = aws_s3_bucket.drift_reports.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ---------------------------------------------------------------------------
# IAM role for the Lambdas (least privilege per task 7.3).
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${local.prefix}-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = local.common_tags
}

data "aws_iam_policy_document" "lambda" {
  # CloudWatch custom metrics.
  statement {
    sid       = "PutMetrics"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"] # PutMetricData does not support resource-level scoping
  }

  # Workshop shortcut (D3): drift-detector forces the drift alarm state.
  statement {
    sid       = "SetDriftAlarmState"
    actions   = ["cloudwatch:SetAlarmState"]
    resources = ["arn:aws:cloudwatch:${var.region}:${data.aws_caller_identity.current.account_id}:alarm:${local.drift_alarm_name}"]
  }

  # Read the reference distribution from the baseline bucket.
  statement {
    sid       = "ReadBaseline"
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = [aws_s3_bucket.baseline.arn, "${aws_s3_bucket.baseline.arn}/*"]
  }

  # Read S1/2 shadow logs (prediction capture).
  statement {
    sid       = "ReadShadowLogs"
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = ["arn:aws:s3:::${local.shadow_logs_bucket}", "arn:aws:s3:::${local.shadow_logs_bucket}/*"]
  }

  # Write Evidently HTML reports.
  statement {
    sid       = "WriteDriftReports"
    actions   = ["s3:PutObject", "s3:GetObject"]
    resources = ["${aws_s3_bucket.drift_reports.arn}/*"]
  }

  # Invoke the SageMaker endpoint (simulators send traffic).
  statement {
    sid       = "InvokeEndpoint"
    actions   = ["sagemaker:InvokeEndpoint"]
    resources = ["arn:aws:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:endpoint/${local.endpoint_name}"]
  }

  # CloudWatch Logs for the functions themselves.
  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"]
  }
}

resource "aws_iam_role_policy" "lambda" {
  name   = "${local.prefix}-lambda"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda.json
}

# ---------------------------------------------------------------------------
# Zip-packaged Lambdas (handler + sibling modules only; pandas via layer).
# ---------------------------------------------------------------------------
data "archive_file" "zip" {
  for_each    = toset(local.zip_lambdas)
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/${each.key}"
  output_path = "${path.module}/build/${each.key}.zip"
}

resource "aws_lambda_function" "drift_detector" {
  function_name    = "drift-detector-${var.attendee_id}"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.11"
  handler          = "handler.handler"
  timeout          = 60
  memory_size      = 512
  filename         = data.archive_file.zip["drift-detector"].output_path
  source_code_hash = data.archive_file.zip["drift-detector"].output_base64sha256
  layers           = [var.pandas_layer_arn]
  environment {
    variables = {
      ATTENDEE_ID        = var.attendee_id
      BASELINE_BUCKET    = local.baseline_bucket
      SHADOW_LOGS_BUCKET = local.shadow_logs_bucket
      DRIFT_ALARM_NAME   = local.drift_alarm_name
      PSI_THRESHOLD      = "0.25"
      WINDOW_MINUTES     = "5"
    }
  }
  tags = local.common_tags
}

resource "aws_lambda_function" "drift_simulator" {
  function_name    = "drift-simulator-${var.attendee_id}"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.11"
  handler          = "handler.handler"
  timeout          = 360
  memory_size      = 512
  filename         = data.archive_file.zip["drift-simulator"].output_path
  source_code_hash = data.archive_file.zip["drift-simulator"].output_base64sha256
  layers           = [var.pandas_layer_arn]
  environment {
    variables = {
      ATTENDEE_ID     = var.attendee_id
      ENDPOINT_NAME   = local.endpoint_name
      BASELINE_BUCKET = local.baseline_bucket
    }
  }
  tags = local.common_tags
}

resource "aws_lambda_function" "incident_simulator" {
  function_name    = "incident-simulator-${var.attendee_id}"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.11"
  handler          = "handler.handler"
  timeout          = 360
  memory_size      = 512
  filename         = data.archive_file.zip["incident-simulator"].output_path
  source_code_hash = data.archive_file.zip["incident-simulator"].output_base64sha256
  layers           = [var.pandas_layer_arn]
  environment {
    variables = {
      ATTENDEE_ID   = var.attendee_id
      ENDPOINT_NAME = local.endpoint_name
    }
  }
  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# Container-image Lambdas (1024 MB; pandas/plotly/scipy in the image).
# ---------------------------------------------------------------------------
resource "aws_lambda_function" "evidently_runner" {
  function_name = "evidently-runner-${var.attendee_id}"
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = var.evidently_image_uri
  timeout       = 300
  memory_size   = 1024
  environment {
    variables = {
      ATTENDEE_ID          = var.attendee_id
      BASELINE_BUCKET      = local.baseline_bucket
      DRIFT_REPORTS_BUCKET = local.drift_reports_buck
      SHADOW_LOGS_BUCKET   = local.shadow_logs_bucket
    }
  }
  tags = local.common_tags
}

resource "aws_lambda_function" "nannyml_runner" {
  function_name = "nannyml-runner-${var.attendee_id}"
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = var.nannyml_image_uri
  timeout       = 300
  memory_size   = 1024
  environment {
    variables = {
      ATTENDEE_ID        = var.attendee_id
      BASELINE_BUCKET    = local.baseline_bucket
      SHADOW_LOGS_BUCKET = local.shadow_logs_bucket
    }
  }
  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# EventBridge schedule: invoke drift-detector every 2 minutes (task 2.3 / D9).
# ---------------------------------------------------------------------------
resource "aws_cloudwatch_event_rule" "drift_detector_schedule" {
  name                = "${local.prefix}-drift-detector"
  description         = "Run drift-detector every 2 minutes for ${var.attendee_id}"
  schedule_expression = "rate(2 minutes)"
  tags                = local.common_tags
}

resource "aws_cloudwatch_event_target" "drift_detector" {
  rule      = aws_cloudwatch_event_rule.drift_detector_schedule.name
  target_id = "drift-detector"
  arn       = aws_lambda_function.drift_detector.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.drift_detector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.drift_detector_schedule.arn
}

# ---------------------------------------------------------------------------
# Attendee role: may invoke the five Session 3 Lambdas (task 7.3).
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "attendee_invoke" {
  statement {
    actions = ["lambda:InvokeFunction"]
    resources = [
      aws_lambda_function.drift_detector.arn,
      aws_lambda_function.drift_simulator.arn,
      aws_lambda_function.incident_simulator.arn,
      aws_lambda_function.evidently_runner.arn,
      aws_lambda_function.nannyml_runner.arn,
    ]
  }
}

resource "aws_iam_policy" "attendee_invoke" {
  name   = "${local.prefix}-attendee-invoke"
  policy = data.aws_iam_policy_document.attendee_invoke.json
  tags   = local.common_tags
}
