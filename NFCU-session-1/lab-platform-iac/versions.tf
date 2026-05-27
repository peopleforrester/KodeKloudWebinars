# MANUAL APPLY ONLY. Do not run from CI.
# This Terraform provisions the demo sandbox; the workshop pipeline workflows assume these resources exist.
# ABOUTME: Terraform and provider version pins for the manually-applied lab sandbox.

terraform {
  required_version = ">= 1.14"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.46.0"
    }
  }
}
