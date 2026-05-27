# ABOUTME: Speaker-owned EKS demo cluster for NFCU Session 4 — VPC, EKS v21, an S3 bucket
# ABOUTME: for model artifacts, and EKS Pod Identity roles for ALB, autoscaler, and KServe.

data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name = var.cluster_name
  azs  = slice(data.aws_availability_zones.available.names, 0, 3)

  # /20 private subnets for workloads, /24 public subnets for the NLB.
  private_subnets = [for i in range(3) : cidrsubnet(var.vpc_cidr, 4, i)]
  public_subnets  = [for i in range(3) : cidrsubnet(var.vpc_cidr, 8, i + 48)]

  bucket_name = var.model_artifacts_bucket_name != "" ? var.model_artifacts_bucket_name : "${var.cluster_name}-models-${data.aws_caller_identity.current.account_id}"

  tags = {
    Project = "nfcu-session-4"
    Session = "4"
  }
}

################################################################################
# VPC
################################################################################

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${local.name}-vpc"
  cidr = var.vpc_cidr

  azs             = local.azs
  private_subnets = local.private_subnets
  public_subnets  = local.public_subnets

  enable_nat_gateway   = true
  single_nat_gateway   = true # One NAT gateway keeps the demo cheap; not HA.
  enable_dns_hostnames = true

  # Tags the AWS Load Balancer Controller uses for subnet auto-discovery.
  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }

  tags = local.tags
}

################################################################################
# EKS cluster (module v21 — note the renamed inputs vs v20)
################################################################################

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = local.name
  kubernetes_version = var.kubernetes_version

  # Public endpoint so the speaker reaches the API from a laptop on demo day.
  endpoint_public_access                   = true
  enable_cluster_creator_admin_permissions = true

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.private_subnets

  addons = {
    coredns    = {}
    kube-proxy = {}
    vpc-cni    = {}
    # Required for EKS Pod Identity — injects credentials into associated pods.
    eks-pod-identity-agent = {}
  }

  eks_managed_node_groups = {
    default = {
      instance_types = [var.node_instance_type]

      min_size     = var.node_min_size
      max_size     = var.node_max_size
      desired_size = var.node_desired_size

      # Cluster Autoscaler auto-discovery tags.
      tags = {
        "k8s.io/cluster-autoscaler/enabled"       = "true"
        "k8s.io/cluster-autoscaler/${local.name}" = "owned"
      }
    }
  }

  tags = local.tags
}

################################################################################
# Model artifacts S3 bucket (private)
################################################################################

resource "aws_s3_bucket" "model_artifacts" {
  bucket = local.bucket_name
  tags   = local.tags
}

resource "aws_s3_bucket_ownership_controls" "model_artifacts" {
  bucket = aws_s3_bucket.model_artifacts.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "model_artifacts" {
  bucket = aws_s3_bucket.model_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "model_artifacts" {
  bucket = aws_s3_bucket.model_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "model_artifacts" {
  bucket = aws_s3_bucket.model_artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

################################################################################
# Read-only S3 policy for the KServe storage initializer
################################################################################

data "aws_iam_policy_document" "kserve_s3_read" {
  statement {
    sid       = "ListBucket"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.model_artifacts.arn]
  }
  statement {
    sid       = "GetObjects"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.model_artifacts.arn}/*"]
  }
}

resource "aws_iam_policy" "kserve_s3_read" {
  name        = "${local.name}-kserve-s3-read"
  description = "Read-only access to the Session 4 model artifacts bucket for the KServe storage initializer."
  policy      = data.aws_iam_policy_document.kserve_s3_read.json
  tags        = local.tags
}

################################################################################
# Pod Identity — KServe storage initializer (reads models from S3)
#
# Unlike IRSA, Pod Identity associations are per (cluster, namespace, service account) —
# there is no namespace wildcard. We bind the demo namespace here; the lab platform creates
# one aws_eks_pod_identity_association per attendee namespace using this same role ARN
# (see cluster/lab-overlays/README.md).
################################################################################

module "pod_identity_kserve_s3" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "~> 2.0"

  name = "${local.name}-kserve-s3-reader"

  additional_policy_arns = { s3 = aws_iam_policy.kserve_s3_read.arn }

  associations = {
    demo = {
      cluster_name    = module.eks.cluster_name
      namespace       = "default"
      service_account = var.kserve_service_account_name
    }
  }

  tags = local.tags
}

################################################################################
# Pod Identity — AWS Load Balancer Controller
################################################################################

module "pod_identity_alb_controller" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "~> 2.0"

  name                            = "${local.name}-alb-controller"
  attach_aws_lb_controller_policy = true

  associations = {
    this = {
      cluster_name    = module.eks.cluster_name
      namespace       = "kube-system"
      service_account = "aws-load-balancer-controller"
    }
  }

  tags = local.tags
}

################################################################################
# Pod Identity — Cluster Autoscaler
################################################################################

module "pod_identity_cluster_autoscaler" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "~> 2.0"

  name                             = "${local.name}-cluster-autoscaler"
  attach_cluster_autoscaler_policy = true
  cluster_autoscaler_cluster_names = [module.eks.cluster_name]

  associations = {
    this = {
      cluster_name    = module.eks.cluster_name
      namespace       = "kube-system"
      service_account = "cluster-autoscaler"
    }
  }

  tags = local.tags
}
