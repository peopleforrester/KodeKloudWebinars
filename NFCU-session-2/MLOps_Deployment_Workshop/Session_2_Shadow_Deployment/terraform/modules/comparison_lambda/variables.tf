# ABOUTME: Inputs for the comparison_lambda module.
# ABOUTME: Function source, both buckets, and the bundled criteria path.
# SPDX-License-Identifier: Apache-2.0

variable "attendee_id" {
  description = "Per-attendee identifier; scopes the function and role names."
  type        = string
}

variable "aws_region" {
  description = "AWS region (used to scope IAM resource ARNs)."
  type        = string
}

variable "account_id" {
  description = "AWS account ID (used to scope IAM resource ARNs)."
  type        = string
}

variable "filename" {
  description = "Path to the deployment package zip."
  type        = string
}

variable "source_code_hash" {
  description = "Base64 SHA256 of the deployment package for change detection."
  type        = string
}

variable "shadow_logs_bucket" {
  description = "Name of the shadow-logs bucket (read)."
  type        = string
}

variable "shadow_logs_bucket_arn" {
  description = "ARN of the shadow-logs bucket (read)."
  type        = string
}

variable "comparison_results_bucket" {
  description = "Name of the comparison-results bucket (read/write)."
  type        = string
}

variable "comparison_results_bucket_arn" {
  description = "ARN of the comparison-results bucket (read/write)."
  type        = string
}

variable "promotion_criteria_path" {
  description = "Path to the promotion-criteria YAML inside the deployment package."
  type        = string
}

variable "tags" {
  description = "Tags applied to taggable resources."
  type        = map(string)
  default     = {}
}
