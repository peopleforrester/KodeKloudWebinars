# MANUAL APPLY ONLY. Do not run from CI.
# This Terraform provisions the demo sandbox; the workshop pipeline workflows assume these resources exist.
# ABOUTME: Provisions the one-time demo sandbox: network, KMS, buckets, ECR, GitHub OIDC,
# ABOUTME: scoped IAM roles, VPC endpoints, and the SageMaker log group.

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

locals {
  account_id     = data.aws_caller_identity.current.account_id
  artifacts_name = "${var.name}-artifacts-${local.account_id}"
  audit_name     = "${var.name}-audit-${local.account_id}"
  oidc_url       = "token.actions.githubusercontent.com"
}

# --- Network -----------------------------------------------------------------
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "${var.name}-vpc" }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]
  tags              = { Name = "${var.name}-private-${var.availability_zones[count.index]}" }
}

resource "aws_security_group" "endpoints" {
  name        = "${var.name}-vpce-sg"
  description = "HTTPS from within the VPC to interface VPC endpoints"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "HTTPS from within the VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "Egress within the VPC fabric"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.name}-vpce-sg" }
}

# Four interface endpoints PRE-provisioned for the demo so the pipeline does not
# create them on every deploy. Same four services as the networking module.
resource "aws_vpc_endpoint" "interface" {
  for_each = toset(["sagemaker.api", "sagemaker.runtime", "ecr.api", "ecr.dkr"])

  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.${var.aws_region}.${each.value}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.endpoints.id]
  private_dns_enabled = true
  tags                = { Name = "${var.name}-vpce-${each.value}" }
}

# --- KMS ---------------------------------------------------------------------
resource "aws_kms_key" "this" {
  description             = "${var.name} model artifact and endpoint encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

resource "aws_kms_alias" "this" {
  name          = "alias/${var.name}-key"
  target_key_id = aws_kms_key.this.key_id
}

# --- S3 buckets (artifacts + audit) -----------------------------------------
resource "aws_s3_bucket" "artifacts" {
  bucket = local.artifacts_name
}

resource "aws_s3_bucket" "audit" {
  bucket = local.audit_name
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_versioning" "audit" {
  bucket = aws_s3_bucket.audit.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.this.arn
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "audit" {
  bucket = aws_s3_bucket.audit.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.this.arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "audit" {
  bucket                  = aws_s3_bucket.audit.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- ECR ---------------------------------------------------------------------
resource "aws_ecr_repository" "this" {
  name                 = var.name
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.this.arn
  }
}

# --- GitHub OIDC provider ----------------------------------------------------
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://${local.oidc_url}"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

# --- Workflow assumer role (GitHub Actions OIDC) -----------------------------
# This role is repo-scoped, not environment-scoped. That is a deliberate lab
# simplification: a single role any branch/environment in this repo can assume.
# The production pattern is two roles PER environment, with the trust condition
# narrowed to a specific environment claim, e.g.:
#   token.actions.githubusercontent.com:sub = repo:<org>/<repo>:environment:production
# so a workflow targeting dev can never assume the production role. The audience is
# pinned to sts.amazonaws.com exactly and the org/repo segments carry no wildcards
# (only the trailing ref/environment segment is wildcarded). See docs/security-pinning.md.
data "aws_iam_policy_document" "workflow_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.oidc_url}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "${local.oidc_url}:sub"
      values   = ["repo:${var.github_org}/${var.github_repo}:*"]
    }
  }
}

resource "aws_iam_role" "workflow" {
  name               = "${var.name}-workflow"
  assume_role_policy = data.aws_iam_policy_document.workflow_trust.json
}

data "aws_iam_policy_document" "workflow_permissions" {
  # SageMaker model/endpoint lifecycle (resource-level support is limited; the
  # workflow role may be broader than the execution role).
  statement {
    sid       = "SageMakerDeploy"
    effect    = "Allow"
    actions   = ["sagemaker:CreateModel", "sagemaker:DeleteModel", "sagemaker:DescribeModel", "sagemaker:CreateEndpointConfig", "sagemaker:DeleteEndpointConfig", "sagemaker:DescribeEndpointConfig", "sagemaker:CreateEndpoint", "sagemaker:UpdateEndpoint", "sagemaker:DeleteEndpoint", "sagemaker:DescribeEndpoint", "sagemaker:InvokeEndpoint", "sagemaker:AddTags", "sagemaker:ListTags"]
    resources = ["arn:aws:sagemaker:${var.aws_region}:${local.account_id}:*"]
  }

  # Pass ONLY the dedicated SageMaker execution role, and only to SageMaker.
  statement {
    sid       = "PassExecutionRole"
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = [aws_iam_role.sagemaker_execution.arn]
    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["sagemaker.amazonaws.com"]
    }
  }

  # ECR: push/pull scoped to the demo repository.
  statement {
    sid       = "EcrRepo"
    effect    = "Allow"
    actions   = ["ecr:BatchCheckLayerAvailability", "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage", "ecr:PutImage", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart", "ecr:CompleteLayerUpload", "ecr:DescribeImages"]
    resources = [aws_ecr_repository.this.arn]
  }

  # ECR auth token is account-wide by AWS design and takes no resource.
  statement {
    sid       = "EcrAuth"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  # S3: artifact and audit buckets (and their objects).
  statement {
    sid       = "Buckets"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
    resources = [aws_s3_bucket.artifacts.arn, "${aws_s3_bucket.artifacts.arn}/*", aws_s3_bucket.audit.arn, "${aws_s3_bucket.audit.arn}/*"]
  }

  # KMS for encrypt/decrypt against the sandbox key.
  statement {
    sid       = "Kms"
    effect    = "Allow"
    actions   = ["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"]
    resources = [aws_kms_key.this.arn]
  }

  # VPC + CloudWatch read/manage for the per-deploy networking module and logs.
  statement {
    sid       = "NetworkAndLogs"
    effect    = "Allow"
    actions   = ["ec2:Describe*", "ec2:CreateVpcEndpoint", "ec2:DeleteVpcEndpoints", "ec2:CreateTags", "logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogGroups", "logs:DescribeLogStreams"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "workflow" {
  name   = "${var.name}-workflow-permissions"
  role   = aws_iam_role.workflow.id
  policy = data.aws_iam_policy_document.workflow_permissions.json
}

# --- SageMaker execution role (separate from the workflow role) --------------
data "aws_iam_policy_document" "sagemaker_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sagemaker_execution" {
  name               = "${var.name}-sagemaker-execution"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_trust.json
}

# Least privilege: every grant below names a specific resource ARN. No wildcards in
# resource ARNs. (ecr:GetAuthorizationToken is the one AWS-mandated exception — it
# operates on no resource — and is isolated in its own statement.)
data "aws_iam_policy_document" "sagemaker_execution" {
  statement {
    sid       = "EcrPull"
    effect    = "Allow"
    actions   = ["ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage", "ecr:BatchCheckLayerAvailability"]
    resources = [aws_ecr_repository.this.arn]
  }

  statement {
    sid       = "EcrAuthToken"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid       = "ArtifactRead"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.artifacts.arn}/*"]
  }

  statement {
    sid       = "KmsDecrypt"
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = [aws_kms_key.this.arn]
  }
}

resource "aws_iam_role_policy" "sagemaker_execution" {
  name   = "${var.name}-sagemaker-execution-permissions"
  role   = aws_iam_role.sagemaker_execution.id
  policy = data.aws_iam_policy_document.sagemaker_execution.json
}

# --- CloudWatch log group ----------------------------------------------------
resource "aws_cloudwatch_log_group" "sagemaker" {
  name              = "/${var.name}/sagemaker"
  retention_in_days = 30
}
