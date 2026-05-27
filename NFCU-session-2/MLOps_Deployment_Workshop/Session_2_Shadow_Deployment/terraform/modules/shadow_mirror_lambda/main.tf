# ABOUTME: shadow-mirror Lambda + IAM + API Gateway v2 HTTP API (POST /predict).
# ABOUTME: Invokes both endpoints and writes shadow logs; fronted by a public URL.
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
  function_name = "shadow-mirror-${var.attendee_id}"
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
    sid    = "InvokeEndpoints"
    effect = "Allow"
    actions = [
      "sagemaker:InvokeEndpoint",
      "sagemaker:InvokeEndpointAsync",
    ]
    resources = [
      var.champion_endpoint_arn,
      var.challenger_endpoint_arn,
    ]
  }
  statement {
    sid    = "WriteShadowLogs"
    effect = "Allow"
    actions = [
      "s3:PutObject",
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
    resources = ["arn:aws:logs:${var.aws_region}:${var.account_id}:log-group:/aws/lambda/${local.function_name}:*"]
  }
}

resource "aws_iam_role_policy" "this" {
  name   = "shadow-mirror"
  role   = aws_iam_role.this.id
  policy = data.aws_iam_policy_document.policy.json
}

# Lab simplifications, documented inline: the function runs outside a VPC, uses
# unencrypted (AES256-account-managed) env vars rather than a KMS CMK, sets no
# reserved concurrency, and is not code-signed. Genuine controls (X-Ray
# tracing, least-privilege IAM) are configured below.
#tfsec:ignore:aws-lambda-enable-tracing
resource "aws_lambda_function" "this" {
  #checkov:skip=CKV_AWS_117:Lambda intentionally not in a VPC for this self-contained lab.
  #checkov:skip=CKV_AWS_173:Env vars use AES256 (no KMS CMK) as a lab simplification.
  #checkov:skip=CKV_AWS_115:No reserved concurrency in the single-attendee lab.
  #checkov:skip=CKV_AWS_272:Code signing is out of scope for the lab.
  #checkov:skip=CKV_AWS_116:DLQ omitted on the synchronous request path (caller sees errors directly).
  function_name    = local.function_name
  role             = aws_iam_role.this.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = var.filename
  source_code_hash = var.source_code_hash
  timeout          = 30
  memory_size      = 256
  tags             = var.tags

  tracing_config {
    mode = "Active"
  }

  environment {
    variables = {
      CHAMPION_ENDPOINT_ARN   = var.champion_endpoint_arn
      CHALLENGER_ENDPOINT_ARN = var.challenger_endpoint_arn
      SHADOW_LOG_BUCKET       = var.shadow_logs_bucket
    }
  }
}

# WAF, access logging, and client-certificate auth on the HTTP API are omitted
# as documented lab simplifications.
#tfsec:ignore:aws-api-gateway-enable-access-logging
resource "aws_apigatewayv2_api" "this" {
  name          = "${local.function_name}-api"
  protocol_type = "HTTP"
  tags          = var.tags
}

resource "aws_apigatewayv2_integration" "this" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.this.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "predict" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "POST /predict"
  target    = "integrations/${aws_apigatewayv2_integration.this.id}"
}

# Access logging on the stage is omitted as a documented lab simplification
# (it would require a dedicated CloudWatch log group and locked-down policy).
#tfsec:ignore:aws-api-gateway-enable-access-logging
resource "aws_apigatewayv2_stage" "default" {
  #checkov:skip=CKV_AWS_76:Access logging omitted as a documented lab simplification.
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true
  tags        = var.tags
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}
