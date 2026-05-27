# ABOUTME: Terraform and provider version constraints for the Session 2 lab root.
# ABOUTME: Pins Terraform >= 1.6 and the AWS provider to the 5.x line.
# SPDX-License-Identifier: Apache-2.0

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}
