# ABOUTME: Input variables for the sagemaker-endpoint module, including the digest-only
# ABOUTME: validation that blocks tag-referenced (mutable) container images.

variable "name" {
  description = "Base name for the SageMaker model, endpoint config, and endpoint."
  type        = string
}

variable "model_data_url" {
  description = "S3 URI of the model artifact tarball (model-v<semver>.tar.gz)."
  type        = string
}

variable "container_image_uri" {
  description = "Inference container image, referenced by immutable digest (…@sha256:<64 hex>)."
  type        = string

  validation {
    # Reject tag-referenced images; only digest references are immutable.
    condition     = can(regex("@sha256:[0-9a-f]{64}$", var.container_image_uri))
    error_message = "container_image_uri must be digest-referenced, e.g. <registry>/<repo>@sha256:<64 hex chars>."
  }
}

variable "execution_role_arn" {
  description = "IAM role assumed by SageMaker. Supplied by the caller — the module never creates or shares a default role."
  type        = string
}

variable "vpc_subnet_ids" {
  description = "Private subnet IDs the endpoint runs in. There is no public ingress path."
  type        = list(string)
}

variable "vpc_security_group_ids" {
  description = "Security group IDs attached to the endpoint's network interfaces."
  type        = list(string)
}

variable "kms_key_arn" {
  description = "KMS key ARN for endpoint storage-volume encryption and model-data decryption."
  type        = string
}

variable "instance_type" {
  description = "SageMaker instance type. Lab/demo default is ml.t3.medium; ml.m6i.large is prod-realistic."
  type        = string
  default     = "ml.t3.medium"
}

variable "instance_count" {
  description = "Number of instances backing the endpoint production variant."
  type        = number
  default     = 1
}
