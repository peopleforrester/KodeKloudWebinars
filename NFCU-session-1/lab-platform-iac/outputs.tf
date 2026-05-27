# MANUAL APPLY ONLY. Do not run from CI.
# This Terraform provisions the demo sandbox; the workshop pipeline workflows assume these resources exist.
# ABOUTME: Sandbox outputs; workflow_role_arn becomes the AWS_ROLE_ARN repo variable.

output "workflow_role_arn" {
  description = "ARN to set as the AWS_ROLE_ARN GitHub Actions repository variable."
  value       = aws_iam_role.workflow.arn
}

output "sagemaker_execution_role_arn" {
  description = "SageMaker execution role ARN (pass to the deploy environments as execution_role_arn)."
  value       = aws_iam_role.sagemaker_execution.arn
}

output "artifacts_bucket" {
  description = "Name of the model artifacts S3 bucket."
  value       = aws_s3_bucket.artifacts.bucket
}

output "audit_bucket" {
  description = "Name of the audit S3 bucket (AUDIT_BUCKET for audit-trail.py)."
  value       = aws_s3_bucket.audit.bucket
}

output "ecr_repository_url" {
  description = "URL of the ECR repository for the inference image."
  value       = aws_ecr_repository.this.repository_url
}

output "kms_key_arn" {
  description = "ARN of the sandbox KMS key."
  value       = aws_kms_key.this.arn
}

output "vpc_id" {
  description = "ID of the sandbox VPC."
  value       = aws_vpc.this.id
}

output "private_subnet_ids" {
  description = "IDs of the two private subnets."
  value       = aws_subnet.private[*].id
}

output "oidc_provider_arn" {
  description = "ARN of the GitHub OIDC identity provider."
  value       = aws_iam_openid_connect_provider.github.arn
}
