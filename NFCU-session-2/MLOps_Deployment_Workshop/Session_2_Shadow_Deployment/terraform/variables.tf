# ABOUTME: Input variables for the Session 2 shadow-deployment Terraform root.
# ABOUTME: Parameterized on attendee_id so each attendee gets isolated resources.
# SPDX-License-Identifier: Apache-2.0

variable "attendee_id" {
  description = "Per-attendee identifier; scopes every resource name in the lab."
  type        = string
}

variable "aws_region" {
  description = "AWS region the lab is provisioned into."
  type        = string
  default     = "us-east-1"
}

variable "champion_endpoint_name" {
  description = <<-EOT
    Name of the already-running champion SageMaker endpoint (from Session 1).
    Left empty by default; a per-attendee value (for example
    workshop-lab-<attendee_id>-production) is supplied at apply time. Terraform
    variable defaults cannot reference other variables, so this is left blank.
  EOT
  type        = string
  default     = ""
}

variable "model_v1_0_1_artifact_s3_uri" {
  description = "S3 URI of the challenger model-v1.0.1 SageMaker model artifact (tar.gz)."
  type        = string
}

variable "sagemaker_image_uri" {
  description = <<-EOT
    ECR image URI for the SageMaker inference container. Defaults to the
    us-east-1 SKLearn 1.2-1 inference image. The account prefix (683313688378)
    is the AWS-published SKLearn image account for us-east-1; change both the
    account and region segments if provisioning in another region.
  EOT
  type        = string
  default     = "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.2-1"
}

variable "tags" {
  description = "Tags merged onto every taggable resource for cost attribution and teardown."
  type        = map(string)
  default = {
    Workshop     = "Session2"
    CostCenter   = "KodeKloud-NFCU"
    AutoTeardown = "2026-06-16"
  }
}
