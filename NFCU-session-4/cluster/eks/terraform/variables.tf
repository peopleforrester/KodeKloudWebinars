# ABOUTME: Input variables for the Session 4 EKS demo cluster, with demo-sane defaults.
# ABOUTME: Override in terraform.tfvars (copy terraform.tfvars.example).

variable "region" {
  description = "AWS region for the demo cluster."
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Name of the EKS cluster. Also used as the teardown confirmation string."
  type        = string
  default     = "nfcu-session-4"
}

variable "kubernetes_version" {
  description = "EKS control plane Kubernetes version (1.34, 1.35, or 1.36)."
  type        = string
  default     = "1.34"
}

variable "node_instance_type" {
  description = "EC2 instance type for the managed node group."
  type        = string
  default     = "m5.xlarge"
}

variable "node_desired_size" {
  description = "Desired node count at apply time."
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum node count the Cluster Autoscaler may scale to."
  type        = number
  default     = 5
}

variable "node_min_size" {
  description = "Minimum node count."
  type        = number
  default     = 2
}

variable "model_artifacts_bucket_name" {
  description = <<-EOT
    S3 bucket name for the XGBoost model artifacts. Leave empty to derive a unique
    name from the cluster name and AWS account ID (recommended — bucket names are global).
  EOT
  type        = string
  default     = ""
}

variable "vpc_cidr" {
  description = "CIDR block for the demo VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "kserve_service_account_name" {
  description = <<-EOT
    ServiceAccount name the KServe storage initializer uses to read model artifacts from
    S3 via IRSA. The trust policy allows this SA name in any namespace (per-attendee
    namespaces), so the lab platform annotates the same SA name everywhere.
  EOT
  type        = string
  default     = "kserve-sa"
}
