# ABOUTME: Provider and Terraform version constraints for the Session 4 EKS demo cluster.
# ABOUTME: EKS module v21; auth via EKS Pod Identity (see main.tf), not IRSA.

terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source = "hashicorp/aws"
      # EKS module v21 and eks-pod-identity v2 require AWS provider v6.
      version = ">= 6.0, < 7.0"
    }
    # Helm and Kubernetes providers are pinned for attendees who extend this module.
    # Add-on installation itself is handled by cluster/addons/bootstrap.sh, not Terraform,
    # so the demo path stays identical between EKS and local kind.
    helm = {
      source  = "hashicorp/helm"
      version = ">= 2.16"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.34"
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
