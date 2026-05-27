# ABOUTME: Outputs for the shadow_log_buckets module.
# ABOUTME: Exposes both bucket names and ARNs to composing configurations.
# SPDX-License-Identifier: Apache-2.0

output "shadow_logs_bucket_name" {
  description = "Name of the shadow-logs bucket."
  value       = aws_s3_bucket.this["shadow_logs"].id
}

output "shadow_logs_bucket_arn" {
  description = "ARN of the shadow-logs bucket."
  value       = aws_s3_bucket.this["shadow_logs"].arn
}

output "comparison_results_bucket_name" {
  description = "Name of the comparison-results bucket."
  value       = aws_s3_bucket.this["comparison_results"].id
}

output "comparison_results_bucket_arn" {
  description = "ARN of the comparison-results bucket."
  value       = aws_s3_bucket.this["comparison_results"].arn
}
