# ABOUTME: Inputs for the traffic_generator_lambda module.
# ABOUTME: Function source, the shadow-mirror URL, and the test-data S3 URIs.
# SPDX-License-Identifier: Apache-2.0

variable "attendee_id" {
  description = "Per-attendee identifier; scopes the function and role names."
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

variable "shadow_mirror_url" {
  description = "Invoke URL of the shadow-mirror API Gateway."
  type        = string
}

variable "shadow_logs_bucket_arn" {
  description = "ARN of the bucket holding the test-data and disagreement-region objects."
  type        = string
}

variable "test_data_uri" {
  description = "S3 URI of the UCI Adult test split JSON."
  type        = string
}

variable "disagreement_region_uri" {
  description = "S3 URI of the disagreement-region row indices JSON."
  type        = string
}

variable "tags" {
  description = "Tags applied to taggable resources."
  type        = map(string)
  default     = {}
}
