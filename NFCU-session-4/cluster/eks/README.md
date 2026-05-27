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
| EKS cluster (`terraform-aws-modules/eks` v21) | Control plane + managed node group + `eks-pod-identity-agent` addon |
| S3 bucket (private, versioned, encrypted) | XGBoost model artifacts |
| Pod Identity role: KServe storage initializer | Reads model artifacts from S3, no static keys |
| Pod Identity role: AWS Load Balancer Controller | Provisions the NLB in front of Kourier |
| Pod Identity role: Cluster Autoscaler | Scales the node group under load |

Auth uses **EKS Pod Identity** (`terraform-aws-modules/eks-pod-identity`), not IRSA — no
OIDC provider, no ServiceAccount role-arn annotations. The agent addon injects credentials
into associated pods. Pod Identity associations are per (namespace, service account): the
ALB controller and autoscaler bind fixed `kube-system` SAs; the KServe storage-initializer
role is bound per attendee namespace (the lab platform creates one association each).

## Version note

- **EKS module v21**, Kubernetes **1.35** (the latest EKS offers as of May 2026 — 1.36 is the
  latest upstream GA but EKS lags; bump the `kubernetes_version` default once EKS adds it).
- **AWS provider v6** is required by the v21 modules.
