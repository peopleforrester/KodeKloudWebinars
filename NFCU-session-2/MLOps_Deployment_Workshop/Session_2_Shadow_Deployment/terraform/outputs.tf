# ABOUTME: Root outputs for the Session 2 shadow-deployment lab.
# ABOUTME: Surfaces the shadow-mirror URL, dashboard, audit bucket, and endpoint.
# SPDX-License-Identifier: Apache-2.0

output "shadow_mirror_invoke_url" {
  description = "Public HTTPS invoke URL for the shadow-mirror API Gateway."
  value       = module.shadow_mirror_lambda.invoke_url
}

output "dashboard_name" {
  description = "Name of the CloudWatch shadow-comparison dashboard."
  value       = module.cloudwatch_dashboard.dashboard_name
}

output "audit_bucket_name" {
  description = "Name of the shared audit-trail S3 bucket."
  value       = module.audit_trail.bucket_name
}

output "challenger_endpoint_name" {
  description = "Name of the challenger SageMaker endpoint."
  value       = aws_sagemaker_endpoint.challenger.name
}
