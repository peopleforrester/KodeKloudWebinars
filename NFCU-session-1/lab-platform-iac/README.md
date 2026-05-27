# Lab platform IaC (manual apply)

**MANUAL APPLY ONLY. Never run from CI.** This Terraform provisions the one-time
demo sandbox the pipeline workflows assume already exists: network, encryption,
buckets, registry, GitHub OIDC, scoped IAM roles, VPC endpoints, and the SageMaker
log group.

## What it provisions

- 1 VPC + 2 private subnets across 2 AZs
- 1 KMS key (alias `nfcu-session-1-key`) with rotation enabled
- 2 S3 buckets — artifacts and audit — named from your AWS account ID, versioned,
  KMS-encrypted, public access fully blocked
- 1 ECR repository (immutable tags, scan-on-push, KMS-encrypted)
- 1 GitHub OIDC identity provider (`token.actions.githubusercontent.com`)
- 1 workflow assumer IAM role, trust scoped to `repo:<org>/<repo>:*`, audience pinned
  to `sts.amazonaws.com`, no wildcards in the org/repo segments
- 1 SageMaker execution role (separate), with ECR-pull / S3-GetObject / KMS-Decrypt
  scoped to specific resource ARNs
- 4 interface VPC endpoints (`sagemaker.api`, `sagemaker.runtime`, `ecr.api`, `ecr.dkr`)
- 1 CloudWatch log group `/nfcu-session-1/sagemaker`

## When to apply

Apply **once**, before the first demo run — and, for attendees, before your fork can
run the pipeline. The workflows do not create any of these resources; they assume
they are present.

```bash
cd NFCU-session-1/lab-platform-iac
cp terraform.tfvars.example terraform.tfvars   # edit for your fork
terraform init
terraform plan
terraform apply
```

## SageMaker service quotas

New accounts frequently need a quota increase before the endpoints will provision:

- **Minimum:** 3 endpoint instances of `ml.t3.medium` per account (dev + staging +
  production each run one instance).
- **Lead time:** quota increase requests on new accounts can take **up to 7 business
  days**. Request the increase well before your session date via Service Quotas →
  Amazon SageMaker → "ml.t3.medium for endpoint usage".

## Fork-time substitutions (replicating at home)

1. Fork `peopleforrester/KodeKloudWebinars` to your own account.
2. In `terraform.tfvars`, set `github_org` and `github_repo` to **your** fork's owner
   and repository name (this scopes the OIDC trust to your repo).
3. `terraform apply`.
4. Copy the `workflow_role_arn` output and set it as the **`AWS_ROLE_ARN` repository
   variable** in your fork (Settings → Secrets and variables → Actions → Variables).
5. Create the three GitHub Environments (`nfcu-session-1-dev`, `-staging`,
   `-production`); add at least one required reviewer to `-production`.

## Cost estimate

- **Per 2-hour demo session:** roughly **$0.30–$0.60** (three `ml.t3.medium` endpoints
  plus negligible S3/KMS/ECR usage).
- **If left running:** about **$130/month**, almost entirely idle endpoint instances.
- **Recommendation:** tear down the endpoints between sessions
  (`terraform destroy` in the environment directories) and keep only the sandbox
  buckets/registry if you want to preserve artifacts and audit history.
