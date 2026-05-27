# ABOUTME: Terraform and provider version constraints for the networking module.
# ABOUTME: Root environments pin the exact provider minor; the module sets a floor.

terraform {
  required_version = ">= 1.14"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0"
    }
  }
}
