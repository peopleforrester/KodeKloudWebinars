# Reproduce on Your Own AWS Account

The lab cluster disappears after the catch-up window. To rebuild the whole session on your
own account, use the EKS Terraform module in [`../cluster/eks/`](../cluster/eks/README.md).
This is the same module the speaker used for the live demo.

## Cost first

**Budget $40–$70 for an 8-hour build-plus-teardown window** with the defaults (2× m5.xlarge,
one NAT gateway, one NLB). The control plane is $0.10/hr; nodes, NAT, and the NLB are the
rest. The full line-item breakdown is in
[`../runbook/speaker-aws-spend.md`](../runbook/speaker-aws-spend.md).

> The single biggest cost mistake is forgetting to tear down. Do `bash cluster/eks/down.sh`
> when you're done — it's a one-liner and it stops the meter.

## Prerequisites

- AWS account + AWS CLI v2 authenticated (`aws sts get-caller-identity` works)
- Terraform ≥ 1.10, `kubectl`, `helm`, `docker`

## Steps (about 40 minutes, mostly waiting on EKS)

```bash
git clone <this repo> && cd NFCU-session-4

# 1. Provision the cluster (~15-25 min)
cd cluster/eks
cp terraform/terraform.tfvars.example terraform/terraform.tfvars   # edit region/sizing if you like
bash up.sh

# 2. Install the add-ons (~10-15 min)
bash ../addons/bootstrap.sh eks
bash ../addons/verify.sh

# 3. Generate and upload the models
python ../../manifests/model-artifacts/generate-xgboost-models.py
bash ../../manifests/model-artifacts/upload-to-s3.sh

# 4. Build/push the TinyLlama image to your ECR
bash ../../predictors/tinyllama/push-to-ecr.sh

# 5. Work the labs (attendee-guide/lab-1 … lab-4), substituting your bucket/image
```

## Tear down (don't skip this)

```bash
cd cluster/eks
bash down.sh        # type the cluster name to confirm
aws eks list-clusters --region us-east-1   # confirm it's gone
```

## No AWS account?

Use the local `kind` path instead — no cloud, no spend:
[`../cluster/local/`](../cluster/local/README.md). It runs labs 1–4 on a 16 GB laptop.
