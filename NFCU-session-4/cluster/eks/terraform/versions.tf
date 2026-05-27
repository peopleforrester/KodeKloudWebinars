# ABOUTME: Provider and Terraform version constraints for the Session 4 EKS demo cluster.
# ABOUTME: EKS module pinned to v20 (v21 dropped native IRSA, which this design relies on).

terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.80, < 6.0"
    }
    # Helm and Kubernetes providers are pinned for attendees who extend this module.
    # Add-on installation itself is handled by cluster/addons/bootstrap.sh, not Terraform,
    # so the demo path stays identical between EKS and local kind.
    helm = {
      source  = "hashicorp/helm"
      version = ">= 2.16, < 3.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.34, < 3.0"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = "nfcu-session-4"
      ManagedBy = "terraform"
    }
  }
}
