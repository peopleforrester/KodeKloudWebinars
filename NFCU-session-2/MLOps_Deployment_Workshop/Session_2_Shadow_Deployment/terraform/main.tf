# ABOUTME: Session 2 shadow-deployment root — composes lambdas, buckets, dashboard,
# ABOUTME: the shared audit_trail module, and the challenger SageMaker endpoint.
# SPDX-License-Identifier: Apache-2.0

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

locals {
  # Every taggable resource carries the four mandatory workshop tags plus any
  # caller-supplied tags. Attendee is computed here since variable defaults
  # cannot reference other variables.
  tags = merge(
    {
      Workshop     = "Session2"
      Attendee     = var.attendee_id
      CostCenter   = "KodeKloud-NFCU"
      AutoTeardown = "2026-06-16"
    },
    var.tags,
  )

  challenger_endpoint_name = "workshop-lab-${var.attendee_id}-challenger"

  # Champion ARN: fall back to a constructed name when champion_endpoint_name is
  # blank so the shadow-mirror IAM policy can still scope to a concrete ARN.
  champion_endpoint_name = (
    var.champion_endpoint_name != ""
    ? var.champion_endpoint_name
    : "workshop-lab-${var.attendee_id}-production"
  )

  champion_endpoint_arn = "arn:aws:sagemaker:${var.aws_region}:${data.aws_caller_identity.current.account_id}:endpoint/${local.champion_endpoint_name}"

  challenger_endpoint_arn = "arn:aws:sagemaker:${var.aws_region}:${data.aws_caller_identity.current.account_id}:endpoint/${local.challenger_endpoint_name}"

  lambda_src = "${path.module}/../lambdas"
}

# ---------------------------------------------------------------------------
# Lambda deployment packages
# ---------------------------------------------------------------------------

data "archive_file" "shadow_mirror" {
  type        = "zip"
  output_path = "${path.module}/build/shadow-mirror.zip"

  source {
    content  = file("${local.lambda_src}/shadow-mirror/handler.py")
    filename = "handler.py"
  }
}

# The comparison package must bundle handler.py, criteria.py, and the promotion
# criteria YAML so PROMOTION_CRITERIA_PATH can resolve inside the task root.
data "archive_file" "comparison" {
  type        = "zip"
  output_path = "${path.module}/build/comparison.zip"

  source {
    content  = file("${local.lambda_src}/comparison/handler.py")
    filename = "handler.py"
  }
  source {
    content  = file("${local.lambda_src}/comparison/criteria.py")
    filename = "criteria.py"
  }
  source {
    content  = file("${path.module}/../config/promotion-criteria.yaml")
    filename = "promotion-criteria.yaml"
  }
}

data "archive_file" "traffic_generator" {
  type        = "zip"
  output_path = "${path.module}/build/traffic-generator.zip"

  source {
    content  = file("${local.lambda_src}/traffic-generator/handler.py")
    filename = "handler.py"
  }
}

# ---------------------------------------------------------------------------
# S3 buckets for shadow logs and comparison results
# ---------------------------------------------------------------------------

module "shadow_log_buckets" {
  source = "./modules/shadow_log_buckets"

  attendee_id = var.attendee_id
  tags        = local.tags
}

# ---------------------------------------------------------------------------
# Shared audit trail (promotion/rollback evidence)
# ---------------------------------------------------------------------------

module "audit_trail" {
  source = "../../../shared/terraform-modules/audit_trail"

  attendee_id = var.attendee_id
  tags        = local.tags
}

# ---------------------------------------------------------------------------
# Challenger SageMaker endpoint
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "sagemaker_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sagemaker_model" {
  name               = "workshop-lab-${var.attendee_id}-challenger-model"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_assume.json
  tags               = local.tags
}

# The challenger reads its model artifact from S3 and writes async inference
# outputs back to the shadow-logs bucket; ECR pull + CloudWatch Logs complete
# the minimal serving permission set.
data "aws_iam_policy_document" "sagemaker_model" {
  statement {
    sid    = "ModelArtifactAndAsyncIO"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = [
      "${module.shadow_log_buckets.shadow_logs_bucket_arn}/*",
    ]
  }
  statement {
    sid    = "ModelArtifactReadAnyBucket"
    effect = "Allow"
    actions = [
      "s3:GetObject",
    ]
    # The model artifact may live in a build/CI bucket outside this root, so the
    # GetObject scope is broad; PutObject above remains scoped to shadow-logs.
    resources = ["arn:aws:s3:::*/*"]
  }
  statement {
    sid    = "EcrPull"
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchCheckLayerAvailability",
    ]
    resources = ["*"]
  }
  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/sagemaker/*"]
  }
}

resource "aws_iam_role_policy" "sagemaker_model" {
  name   = "challenger-serving"
  role   = aws_iam_role.sagemaker_model.id
  policy = data.aws_iam_policy_document.sagemaker_model.json
}

resource "aws_sagemaker_model" "challenger" {
  name               = "workshop-lab-${var.attendee_id}-challenger"
  execution_role_arn = aws_iam_role.sagemaker_model.arn
  tags               = local.tags

  primary_container {
    image          = var.sagemaker_image_uri
    model_data_url = var.model_v1_0_1_artifact_s3_uri
  }
}

resource "aws_sagemaker_endpoint_configuration" "challenger" {
  name = "workshop-lab-${var.attendee_id}-challenger"
  tags = local.tags

  production_variants {
    variant_name           = "challenger"
    model_name             = aws_sagemaker_model.challenger.name
    initial_instance_count = 1
    instance_type          = "ml.m5.xlarge"
  }
}

# A customer-managed KMS volume key is omitted as a documented lab
# simplification; production would set kms_key_arn on the endpoint config.
#tfsec:ignore:aws-sagemaker-enable-endpoint-config-encryption
resource "aws_sagemaker_endpoint" "challenger" {
  name                 = local.challenger_endpoint_name
  endpoint_config_name = aws_sagemaker_endpoint_configuration.challenger.name
  tags                 = local.tags
}

# ---------------------------------------------------------------------------
# Lambda modules
# ---------------------------------------------------------------------------

module "shadow_mirror_lambda" {
  source = "./modules/shadow_mirror_lambda"

  attendee_id             = var.attendee_id
  aws_region              = var.aws_region
  account_id              = data.aws_caller_identity.current.account_id
  filename                = data.archive_file.shadow_mirror.output_path
  source_code_hash        = data.archive_file.shadow_mirror.output_base64sha256
  champion_endpoint_arn   = local.champion_endpoint_arn
  challenger_endpoint_arn = local.challenger_endpoint_arn
  shadow_logs_bucket      = module.shadow_log_buckets.shadow_logs_bucket_name
  shadow_logs_bucket_arn  = module.shadow_log_buckets.shadow_logs_bucket_arn
  tags                    = local.tags
}

module "comparison_lambda" {
  source = "./modules/comparison_lambda"

  attendee_id                   = var.attendee_id
  aws_region                    = var.aws_region
  account_id                    = data.aws_caller_identity.current.account_id
  filename                      = data.archive_file.comparison.output_path
  source_code_hash              = data.archive_file.comparison.output_base64sha256
  shadow_logs_bucket            = module.shadow_log_buckets.shadow_logs_bucket_name
  shadow_logs_bucket_arn        = module.shadow_log_buckets.shadow_logs_bucket_arn
  comparison_results_bucket     = module.shadow_log_buckets.comparison_results_bucket_name
  comparison_results_bucket_arn = module.shadow_log_buckets.comparison_results_bucket_arn
  promotion_criteria_path       = "promotion-criteria.yaml"
  tags                          = local.tags
}

module "traffic_generator_lambda" {
  source = "./modules/traffic_generator_lambda"

  attendee_id            = var.attendee_id
  filename               = data.archive_file.traffic_generator.output_path
  source_code_hash       = data.archive_file.traffic_generator.output_base64sha256
  shadow_mirror_url      = module.shadow_mirror_lambda.invoke_url
  shadow_logs_bucket_arn = module.shadow_log_buckets.shadow_logs_bucket_arn
  test_data_uri          = "s3://${module.shadow_log_buckets.shadow_logs_bucket_name}/test-data/adult-test.json"
  disagreement_region_uri = "s3://${module.shadow_log_buckets.shadow_logs_bucket_name}/test-data/disagreement-region.json"
  tags                    = local.tags
}

module "cloudwatch_dashboard" {
  source = "./modules/cloudwatch_dashboard"

  attendee_id = var.attendee_id
  aws_region  = var.aws_region
}
