# ABOUTME: Input variables for the staging environment. Sessions 1's environments differ only
# ABOUTME: by `name` and the workflow-injected `model_version`.

variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "name" {
  description = "Environment-scoped resource name prefix."
  type        = string
  default     = "nfcu-session-1-staging"
}

variable "model_version" {
  description = "Immutable model semver injected by the deploy workflow (e.g. 1.0.0)."
  type        = string
}

variable "container_image_uri" {
  description = "Digest-referenced inference image (…@sha256:<64 hex>)."
  type        = string
}

variable "model_data_url" {
  description = "S3 URI of the model artifact tarball for this version."
  type        = string
}

variable "execution_role_arn" {
  description = "SageMaker execution role ARN (provisioned by lab-platform-iac)."
  type        = string
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption and model-data decryption."
  type        = string
}

variable "instance_type" {
  description = "SageMaker hosting instance type."
  type        = string
  default     = "ml.t3.medium"
}
