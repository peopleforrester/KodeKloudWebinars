# ABOUTME: Input variables for the per-attendee NFCU Session 3 infrastructure.
# ABOUTME: One Terraform workspace per attendee; attendee_id parameterizes names.

variable "attendee_id" {
  description = "Attendee sandbox id, e.g. lab-007. Drives all per-attendee resource names."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]{3,40}$", var.attendee_id))
    error_message = "attendee_id must be 3-40 chars of lowercase letters, digits, or hyphens."
  }
}

variable "region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "shadow_logs_bucket" {
  description = "Bucket holding S1/2 prediction (shadow) logs the detector reads. Defaults to the per-attendee convention; override if S1/2 uses a different name."
  type        = string
  default     = ""
}

variable "pandas_layer_arn" {
  description = "ARN of the AWS SDK for pandas managed Lambda layer (provides pandas/numpy/pyarrow to the zip Lambdas)."
  type        = string
  # Region-specific managed layer; default targets us-east-1, Python 3.11.
  default = "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python311:13"
}

variable "evidently_image_uri" {
  description = "ECR image URI for the evidently-runner container Lambda."
  type        = string
  default     = "PLACEHOLDER.dkr.ecr.us-east-1.amazonaws.com/nfcu-session-3/evidently-runner:latest"
}

variable "nannyml_image_uri" {
  description = "ECR image URI for the nannyml-runner container Lambda."
  type        = string
  default     = "PLACEHOLDER.dkr.ecr.us-east-1.amazonaws.com/nfcu-session-3/nannyml-runner:latest"
}

variable "endpoint_name" {
  description = "SageMaker endpoint the simulators target. Defaults to the S1/2 production endpoint convention."
  type        = string
  default     = ""
}
