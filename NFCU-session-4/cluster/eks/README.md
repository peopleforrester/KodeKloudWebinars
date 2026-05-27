# EKS Demo Cluster (Terraform)

A speaker-owned EKS cluster for the live Session 4 demo, and the same module attendees
can use to reproduce the session on their own AWS account afterward. CPU-only, sized for
a 2-hour workshop, and designed to be torn down the same day.

This is the live-demo path. To rehearse without AWS spend, use `../local/` (kind).

## Prerequisites

- An AWS account with permissions to create VPC, EKS, IAM, and S3 resources
- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html), authenticated (`aws sts get-caller-identity` works)
- [Terraform](https://developer.hashicorp.com/terraform/install) ≥ 1.10
- `kubectl` ≥ 1.30 and `helm` ≥ 3.14 (for the add-ons bootstrap)

## Cost

With the defaults (2× `m5.xlarge`, single NAT gateway, one NLB) budget **$40–$70 for an
8-hour rehearsal-plus-session window**. The control plane is $0.10/hr; nodes, the NAT
gateway, and the NLB are the rest. Full line-item breakdown:
[`../../runbook/speaker-aws-spend.md`](../../runbook/speaker-aws-spend.md).

> The single largest cost risk is forgetting to tear down. `down.sh` is on the
> post-session checklist for exactly this reason.

## Day-of procedure

```bash
cd cluster/eks
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# edit terraform.tfvars if you want a different region or sizing

bash up.sh                       # terraform init + plan + apply (~15-25 min)
bash ../addons/bootstrap.sh eks  # install Knative, KServe, OpenCost, etc.
bash ../addons/verify.sh         # confirm everything is Ready

# upload model artifacts to the Terraform-created S3 bucket
bash ../../manifests/model-artifacts/generate-xgboost-models.py
bash ../../manifests/model-artifacts/upload-to-s3.sh
```

## Teardown procedure

```bash
cd cluster/eks
bash down.sh    # prompts for the cluster name, then terraform destroy
```

`down.sh` refuses to destroy unless you type the exact cluster name. After it finishes,
confirm nothing remains:

```bash
aws eks list-clusters --region us-east-1
```

## What Terraform creates

| Resource | Purpose |
|---|---|
| VPC (`terraform-aws-modules/vpc`, 3 AZs, 1 NAT) | Network for the cluster |
| EKS cluster (`terraform-aws-modules/eks` v20) | Control plane + managed node group |
| S3 bucket (private, versioned, encrypted) | XGBoost model artifacts |
| IRSA role: KServe storage initializer | Reads model artifacts from S3, no static keys |
| IRSA role: AWS Load Balancer Controller | Provisions the NLB in front of Kourier |
| IRSA role: Cluster Autoscaler | Scales the node group under load |

## Version note

The EKS module is pinned to **v20**. Version 21 removed native IRSA support in favor of
EKS Pod Identity; because the whole storage/ingress/autoscaling design here is IRSA-based,
upgrading past v20 is a separate change (migrate the three roles to Pod Identity
associations). See `versions.tf`.
