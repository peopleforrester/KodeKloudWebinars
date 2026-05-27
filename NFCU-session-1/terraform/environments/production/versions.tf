# ABOUTME: Terraform and provider version pins for the production environment composition.
# ABOUTME: Provider is locked to a specific minor; required_version excludes EOL <1.14.

terraform {
  # Terraform 1.13 reached end-of-life on 2026-04-29; require 1.14+ (1.15.x recommended).
  required_version = ">= 1.14"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.46.0"
    }
  }
}
