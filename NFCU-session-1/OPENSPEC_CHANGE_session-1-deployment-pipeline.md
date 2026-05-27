# Spec: Bootstrap `NFCU-session-1/` in KodeKloudWebinars

**Target repo**: `git@github.com:peopleforrester/KodeKloudWebinars.git`
**Branch**: feature branch off `main`
**New top-level directory**: `NFCU-session-1/`
**Live-demo single-user model** — Michael demos from his own AWS sandbox. Attendees clone and replicate at home. Not a hosted 30-attendee workshop.

Hand this whole file to Claude Code via `/goal` and have it build out the directory, the runnable code, the Terraform, the workflows, and the docs.

---

## 1. Why this exists

Michael delivers a four-session live-demo webinar series on ML model deployment for DevOps engineers, starting Session 1 on June 2, 2026. The narrative spine is one question:

> **"Can you trace any prediction your model made, all the way back to the data it was trained on, in under five minutes?"**

Today the repo contains only `Agentic_DevOps/` (markdown collateral). There's no Session 1 directory, no runnable Terraform, no workflows, no scripts. Without this change there's no live demo and no take-home repo.

Future sessions (`NFCU-session-2/`, `NFCU-session-3/`, `NFCU-session-4/`) will land as separate top-level directories using the same pattern. This spec only builds Session 1, plus stub READMEs for Sessions 2–4.

---

## 2. What lands where

### 2.1 New top-level directories

```
KodeKloudWebinars/
├── Agentic_DevOps/             # UNCHANGED
├── NFCU-session-1/             # NEW — fully populated by this spec
├── NFCU-session-2/             # NEW — stub README only
├── NFCU-session-3/             # NEW — stub README only
├── NFCU-session-4/             # NEW — stub README only
├── .github/workflows/          # NEW directory; three workflow files added
├── README.md                   # MODIFIED — add Session 1 entry
├── CLAUDE.md                   # MODIFIED — note hybrid stack
└── .gitignore                  # MODIFIED — add Python + Terraform patterns
```

### 2.2 `NFCU-session-1/` internal layout

```
NFCU-session-1/
├── README.md                       # folder entry point, role-based starting points
├── LAB_GUIDE.md                    # attendee post-webinar walkthrough
├── FAQ.md                          # nine anticipated questions
├── session-outline.md              # presenter outline (public-safe, no NFCU references in body text)
├── resources.md                    # annotated reading list
├── requirements.txt                # Python deps pinned with ==
├── docs/
│   ├── reference-card.md           # one-printed-page take-home
│   ├── security-pinning.md         # Trivy March 2026 incident + pin-by-SHA syntax
│   └── cross-session-continuity.md # what Sessions 2-4 consume from Session 1
├── terraform/
│   ├── modules/
│   │   ├── sagemaker-endpoint/     # main.tf, variables.tf, outputs.tf, versions.tf, README.md
│   │   └── networking/             # same five files
│   └── environments/
│       ├── dev/                    # main.tf, variables.tf, outputs.tf, versions.tf, backend.tf, terraform.tfvars.example
│       ├── staging/                # same six files
│       └── production/             # same six files
├── pipeline/
│   ├── validate.py
│   ├── audit-trail.py
│   ├── build-container.sh
│   ├── verify-container.sh
│   └── Dockerfile
├── scripts/
│   └── train-sample-model.py
├── tests/
│   └── smoke/
│       ├── sample-payload.json
│       └── known-input-output.json
└── lab-platform-iac/               # manually applied, NOT CI-applicable
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── versions.tf
    ├── terraform.tfvars.example
    └── README.md
```

### 2.3 Workflow files at repo root (GitHub requires this)

GitHub Actions only reads workflows from `.github/workflows/` at the repo root, not from subdirectories. So:

```
.github/workflows/
├── nfcu-session-1-deploy-dev.yml
├── nfcu-session-1-deploy-staging.yml
└── nfcu-session-1-deploy-production.yml
```

Each is path-filtered to only trigger on changes to `NFCU-session-1/**` and `.github/workflows/nfcu-session-1-*.yml`. Filename prefix namespaces them away from any future webinar's workflows.

---

## 3. Constraints — non-negotiable

| Thing | Value | Why |
|---|---|---|
| AWS region | `us-east-1` | SageMaker public image availability, service quotas |
| Terraform | `>= 1.14` (recommend 1.15.x) | v1.13 reached EOL April 29, 2026 |
| Cosign | `>= 3.0` | v2 maintenance-only; v3 introduced breaking change for `sign-blob` requiring `--bundle` |
| Trivy | `>= 0.70.0`. Explicitly blocked: `v0.69.4`, `v0.69.5`, `v0.69.6` | March 19, 2026 supply chain compromise (poisoned binaries) |
| Container base image | `683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1` | Referenced by SHA256 digest in Dockerfile; tag is comment only |
| Python | 3.11 | Matches SageMaker XGBoost 1.7-1 container |
| Sample dataset | UCI Adult Census (`archive.ics.uci.edu/dataset/2/adult`, CC BY 4.0) | Canonical small ML binary classification example |
| SageMaker instance type | `ml.t3.medium` (lab/demo); document `ml.m6i.large` as prod-realistic | Not previous-gen `ml.t2.medium`, not over-spec `ml.m5.large` |
| Third-party Action pinning | Full 40-char commit SHA. No tags. | March 2026 Trivy action tag force-push incident |
| GitHub-owned action pinning | Major version tag (`@v4`) acceptable | GitHub controls the repo |
| Model version references | Immutable semver only | Mutable identifiers rejected by `validate.py` |

---

## 4. Do NOT do

- Do **not** apply any Terraform against AWS. Generate files; never `terraform apply`.
- Do **not** create or push to GitHub. Generate files in the working tree.
- Do **not** generate AWS credentials, GitHub tokens, KMS material, or any secret.
- Do **not** touch any file under `Agentic_DevOps/`.
- Do **not** "improve" the UCI Adult sample model with bias correction. Its limitations are intentional and documented in the model card.
- Do **not** upgrade pinned tool versions to newer releases discovered at execution time. Note them in comments; use the pinned values.

---

## 5. Capability 1: Pipeline validation (`validate.py`)

**File**: `NFCU-session-1/pipeline/validate.py` (Python 3.11)

Three independent checks, each with a distinct exit code:

| Check | Exit code | Log line on failure |
|---|---|---|
| Schema validation | 1 | `VALIDATION FAILED: Schema check — {specific field/error}` |
| Mutable reference rejection | 2 | `VALIDATION FAILED: Mutable artifact reference — '{value}' is not allowed; use immutable semver` |
| Policy check | 3 | `VALIDATION FAILED: Policy check — {specific missing requirement}` |
| Internal error | 99 | `VALIDATION ERROR: Internal — {exception class}: {message}` |
| All pass | 0 | `VALIDATION PASSED: schema, reference, policy` |

**Rules**:

- Mutable reference check rejects (case-insensitive): `latest`, `prod`, `current`, `stable`, `main`. After rejection, no later checks run.
- Schema check validates extracted `signature.json` against the documented schema (see §11).
- Policy check enforces three sub-rules: `model_card.md` is at least 100 bytes; `metadata.json` contains `training_run_id`, `training_dataset`, `evaluation`; `evaluation.accuracy >= 0.5`.
- Unhandled exceptions are caught at the top level and re-emitted with exit code 99 and the `VALIDATION ERROR:` log prefix. Validation never silently passes.
- Script accepts `--artifact s3://...` (requires AWS creds) or `--artifact file:///path/...` (offline). It also reads `--model-version` for the mutable-ref check. Both can also be provided via env vars `ARTIFACT_URI` and `MODEL_VERSION` for CI use.

**The Lab 1 deliberate-failure path**: when an attendee follows the lab guide and sets `model_version = "latest"` in `terraform/environments/dev/terraform.tfvars`, the GitHub Actions UI must show the `VALIDATION FAILED: Mutable artifact reference — 'latest' is not allowed; use immutable semver` line as the visible failure cause. Don't bury this in a long traceback.

---

## 6. Capability 2: Container build, scan, sign (`build-container.sh`, `verify-container.sh`, `Dockerfile`)

**Files**: `NFCU-session-1/pipeline/build-container.sh`, `verify-container.sh`, `Dockerfile`

**Dockerfile**:
- `FROM 683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost@sha256:<digest>  # 1.7-1` (tag is comment only)
- Copies model artifact tarball contents into `/opt/ml/model/`
- Sets the inference entrypoint per SageMaker XGBoost container conventions
- Image, when run with `docker run -p 8080:8080`, must respond 200 OK to `GET /ping`

**`build-container.sh`**:
1. First step verifies `trivy --version` reports `>= 0.70.0` and `cosign version` reports `>= 3.0.0`. Fail fast if not.
2. `docker build` the image.
3. `trivy image --severity HIGH,CRITICAL --exit-code 1 <image>` — any HIGH or CRITICAL fails the script (and the workflow).
4. `cosign sign --key awskms://<key-id> <image>` — pushes signature to ECR as OCI artifact.
5. `docker push <image>` — pushed with both a human-readable tag (`v1.0.0`) and the SHA256 digest.
6. Emit the digest to `$GITHUB_OUTPUT` as `image_digest=sha256:<hex>` for downstream jobs.

**`verify-container.sh`**:
- Runs `cosign verify --key awskms://<key-id> <image>` before any Terraform action.
- Exit non-zero if verification fails. Deploy workflow gates `terraform plan`/`apply` on this step's success.

**Pinning**: any GitHub Action installing Trivy must be pinned by full 40-char commit SHA. Never `aquasecurity/trivy-action@v1` or `@main` or any version tag. Same for `aquasecurity/setup-trivy`. The `docs/security-pinning.md` file explains why (the March 2026 incident).

---

## 7. Capability 3: Audit trail (`audit-trail.py`)

**File**: `NFCU-session-1/pipeline/audit-trail.py`

Runs as the final step of the production deploy workflow. Writes one JSON object to S3 at:

```
s3://<audit-bucket>/audit/{YYYY-MM-DD}/{git_commit_sha}.json
```

**Required fields** (all non-null, in this order at the top of the JSON):

```json
{
  "schema_version": 1,
  "timestamp": "<ISO-8601 UTC>",
  "event": "production_deploy_completed",
  "endpoint_arn": "...",
  "endpoint_version": "1.0.0",
  "container_digest": "sha256:...",
  "artifact_version": "1.0.0",
  "artifact_s3_uri": "s3://.../model-v1.0.0.tar.gz",
  "training_run_id": "...",
  "training_dataset": "uci-adult-2024-snapshot",
  "git_commit_sha": "...",
  "git_repo": "peopleforrester/KodeKloudWebinars",
  "approver_identity": "<github actor>",
  "change_ticket_reference": "<from workflow input>",
  "deployment_workflow_run_url": "<computed from $GITHUB_*>"
}
```

**Behavior**:
- Reads its inputs from env vars (`GITHUB_*` plus `MODEL_VERSION`, `CONTAINER_DIGEST`, `ARTIFACT_S3_URI`, `TRAINING_RUN_ID`, `TRAINING_DATASET`, `APPROVER_IDENTITY`, `CHANGE_TICKET_REFERENCE`).
- On S3 transient 5xx: retry with exponential backoff, 5 attempts max, ~30s total. If all fail, workflow step fails — deploy is NOT marked successful without the audit event.
- `schema_version: 1` is the first key. Future sessions/changes that alter the schema bump this number.

**The five-minute trace test**: a developer must be able to take any prediction made by the prod endpoint and trace it back to its training run in under five minutes using only `aws` CLI and `jq` against this audit bucket. The trace procedure is documented step-by-step in `docs/cross-session-continuity.md`.

---

## 8. Capability 4: Terraform modules

### 8.1 `terraform/modules/sagemaker-endpoint/`

**Required inputs**: `name`, `model_data_url`, `container_image_uri` (must be digest-referenced; module should validate the format), `execution_role_arn`, `vpc_subnet_ids`, `vpc_security_group_ids`, `kms_key_arn`.

**Optional inputs (with safe defaults)**: `instance_type` (default `ml.t3.medium`), `instance_count` (default `1`).

**Security defaults built into the module** (not in documentation):
- `VpcConfig.Subnets` always set from the supplied private subnet IDs. No path for inbound public traffic.
- `KmsKeyId` set on both the endpoint config and the `aws_sagemaker_model` resource (for `ModelDataUrl` decryption).
- Execution role is an input — module does NOT create or assume a shared "default" role. A code comment explains this is intentional.
- `DeploymentConfig.RollingUpdatePolicy` set with `MaximumExecutionTimeoutInSeconds = 3600` and `WaitIntervalInSeconds = 60`. A comment points the reader at where the rollback mechanism lives.

**Module README** lists inputs, outputs, and has a "Security guarantees" section enumerating the defaults.

### 8.2 `terraform/modules/networking/`

VPC with 2 private subnets across 2 AZs in the target region. VPC endpoints for each of:
- `com.amazonaws.us-east-1.sagemaker.api`
- `com.amazonaws.us-east-1.sagemaker.runtime`
- `com.amazonaws.us-east-1.ecr.api`
- `com.amazonaws.us-east-1.ecr.dkr`

Endpoints attached to the same private subnets the SageMaker endpoints will run in.

### 8.3 Environment compositions

Three working directories: `terraform/environments/{dev,staging,production}/`. Each composes the two modules with environment-specific inputs. Each has:
- `main.tf`, `variables.tf`, `outputs.tf`
- `versions.tf` declaring `required_version = ">= 1.14"` and pinned `required_providers` (AWS provider locked to a specific minor version)
- `backend.tf` with an S3 backend; bucket name templated from a CI-supplied variable; unique S3 key per environment
- `terraform.tfvars.example` with placeholders (no real tfvars committed)

For Session 1, dev/staging/production differ only by `name` and the `model_version` injected by the workflow. Sessions 2–4 will diverge them (champion-challenger, monitoring, KServe). Aligning them now is intentional.

---

## 9. Capability 5: GitHub Actions workflows

Three files at repo root `.github/workflows/`. All workflows:
- Use OIDC for AWS access. Role ARN from `${{ vars.AWS_ROLE_ARN }}`. No `aws-access-key-id` / `aws-secret-access-key` anywhere in any workflow.
- Declare `permissions: id-token: write, contents: read`. No broader.
- Pin every third-party action by full 40-char commit SHA, with the corresponding tag in an inline comment for readability. GitHub-owned actions (`actions/*`, `aws-actions/*`) may use major version tags.
- Have `paths:` filters scoping triggers to `NFCU-session-1/**` and `.github/workflows/nfcu-session-1-*.yml`.

### 9.1 `nfcu-session-1-deploy-dev.yml`

- Trigger: push to `main` with path filter match.
- Jobs: validate → (optional) containerize → terraform apply (dev environment).
- Container stage gated by `env.ENABLE_CONTAINER_STAGE: "false"` at workflow level. Comment explains lab guide tells user to flip to `"true"` after validation is understood.
- Validation job runs `validate.py` and surfaces its log line as the visible failure cause on red runs.

### 9.2 `nfcu-session-1-deploy-staging.yml`

- Trigger: PR merge from `promote-to-staging` branch into `main` with path filter match.
- Jobs: validate → verify-container (against the digest from the dev build, do NOT rebuild) → terraform apply (staging).

### 9.3 `nfcu-session-1-deploy-production.yml`

- Trigger: `workflow_dispatch` only. Required input `change_ticket_reference` (string).
- Bound to `nfcu-session-1-production` GitHub Environment with at least one required reviewer.
- First step validates `change_ticket_reference` against regex `^(LAB|CHG|TICKET|DEMO)-[0-9]+$`. Fail workflow on no match.
- Job sequence: regex check → validate → verify-container → terraform apply (production) → `audit-trail.py`.
- Implements an "approver ≠ PR-author" workflow step that queries the GitHub API for the most recent merge commit's author and compares against `github.actor`. The step is preceded by a comment block explaining: during the live demo Michael typically triggers his own production deploy and verbally acknowledges this check would block in prod; LAB_GUIDE.md tells attendees how to use two accounts to exercise the check at home.

### 9.4 GitHub Environments

The repo's GitHub Environment settings (configured manually, post-merge, documented in `LAB_GUIDE.md` and `lab-platform-iac/README.md`):
- `nfcu-session-1-dev` — no required reviewers
- `nfcu-session-1-staging` — no required reviewers
- `nfcu-session-1-production` — at least one required reviewer

---

## 10. Capability 6: Lab platform IaC (`lab-platform-iac/`)

**This is manually applied, never from CI.** Every `.tf` file starts with:

```hcl
# MANUAL APPLY ONLY. Do not run from CI.
# This Terraform provisions the demo sandbox; the workshop pipeline workflows assume these resources exist.
```

Parameterized by `github_org` (default `peopleforrester`), `github_repo` (default `KodeKloudWebinars`), `aws_region` (default `us-east-1`).

**Provisions one AWS sandbox**:
- 1 VPC + 2 private subnets across 2 AZs
- 1 KMS key, alias `nfcu-session-1-key`
- 2 S3 buckets: artifacts + audit. Names derived from AWS account ID for uniqueness.
- 1 ECR repository
- 1 GitHub OIDC identity provider at `token.actions.githubusercontent.com`
- 1 IAM role (workflow assumer) with trust policy scoped to `repo:peopleforrester/KodeKloudWebinars:*`
  - `aud` claim: `sts.amazonaws.com` exactly
  - No wildcards in org or repo segments
  - Comment block above the resource explains: this is repo-scoped not environment-scoped, deliberate lab simplification; production pattern is two roles per environment with `:environment:production` scoping; points reader at `docs/security-pinning.md`
- 1 SageMaker execution role (separate from the workflow role). Permissions:
  - ECR pull scoped to the specific ECR repo ARN
  - S3 GetObject scoped to artifact bucket ARN
  - KMS Decrypt scoped to the specific KMS key ARN
  - No wildcards in resource ARNs
- 4 VPC endpoints (the same four as the networking module — these are PRE-provisioned here for the demo, NOT applied each deploy)
- 1 CloudWatch log group `/nfcu-session-1/sagemaker`

**`lab-platform-iac/README.md`** documents:
- When to apply (once, before first demo run; before forking attendees can run the pipeline)
- Required SageMaker service quotas: 3 endpoint instances of `ml.t3.medium` minimum per account, 7-business-day lead time for quota increase requests on new accounts
- Fork-time substitutions for attendees replicating at home: their `github_org`, `github_repo`, and how to set the `AWS_ROLE_ARN` repo variable after apply
- Cost estimate: $0.30–$0.60 per 2-hour demo session; ~$130/month if left running (mostly idle endpoints); tear-down recommendation between sessions

---

## 11. Capability 7: Sample model + training script

**File**: `NFCU-session-1/scripts/train-sample-model.py`

Downloads UCI Adult Census, trains XGBoost binary classifier predicting `income > $50K` with `max_depth=6, n_estimators=100, learning_rate=0.1, random_state=42`. Deterministic — two runs on identical hardware produce a `model-v1.0.0.tar.gz` with the same SHA256.

Supports `--dry-run` mode that exercises data download + preprocessing without writing the artifact (used by Phase 7 verification).

**Output**: `model-v1.0.0.tar.gz` containing exactly five files:

### 11.1 `model-v1.0.0/model.xgb`
Serialized XGBoost model.

### 11.2 `model-v1.0.0/inference.py`
SageMaker inference entrypoint conforming to SageMaker XGBoost container conventions.

### 11.3 `model-v1.0.0/signature.json`
```json
{
  "input": {
    "type": "object",
    "properties": {
      "age": {"type": "integer"},
      "workclass": {"type": "string"},
      "education": {"type": "string"},
      "marital_status": {"type": "string"},
      "occupation": {"type": "string"},
      "race": {"type": "string"},
      "sex": {"type": "string"},
      "hours_per_week": {"type": "integer"}
    },
    "required": ["age", "hours_per_week"]
  },
  "output": {
    "type": "object",
    "properties": {
      "income_over_50k": {"type": "boolean"},
      "probability": {"type": "number"}
    }
  }
}
```

### 11.4 `model-v1.0.0/metadata.json`
```json
{
  "model_name": "uci-adult-income-classifier",
  "model_version": "1.0.0",
  "training_run_id": "<computed at build time, format: train-YYYY-MM-DD-<hex8>>",
  "training_dataset": "uci-adult-2024-snapshot",
  "training_dataset_sha256": "<computed at build time>",
  "hyperparameters": {"max_depth": 6, "n_estimators": 100, "learning_rate": 0.1},
  "evaluation": {"accuracy": 0.86, "f1_score": 0.71}
}
```

### 11.5 `model-v1.0.0/model_card.md`
~200 words. Must include a `## Known limitations` section that explicitly names `race`, `sex`, `marital_status` as features included in the model and states this dataset is not appropriate for credit-risk modeling — it's used as a teaching example for binary classification. Total file size at least 100 bytes (policy check threshold).

### 11.6 Smoke test fixtures

`NFCU-session-1/tests/smoke/sample-payload.json`:
```json
{
  "age": 39, "workclass": "Private", "education": "Bachelors",
  "marital_status": "Never-married", "occupation": "Prof-specialty",
  "race": "White", "sex": "Male", "hours_per_week": 40
}
```

`NFCU-session-1/tests/smoke/known-input-output.json`:
```json
{
  "input": { ...same fields as sample-payload... },
  "expected_output": {"income_over_50k": false, "probability_range": [0.15, 0.35]}
}
```

### 11.7 `requirements.txt`
Pinned with `==`: `xgboost`, `pandas`, `numpy`, `scikit-learn`, `boto3`, `jsonschema`. Specific patch versions (e.g., `xgboost==2.0.3`), not ranges.

---

## 12. Capability 8: Documentation

### 12.1 `NFCU-session-1/README.md`
Folder entry point. Sections:
- Title + one-paragraph series overview
- "What's here" Markdown table (one row per top-level file/folder, with audience)
- "Start Here" role-based entry points:
  - "I'm watching the live demo on June 2" → link to `session-outline.md`
  - "I want to run this myself after the webinar" → link to `LAB_GUIDE.md` + `lab-platform-iac/README.md`
  - "I'm running my own webinar from this material" → link to `session-outline.md` + the docs/ folder
- "Required tool versions" section (Terraform, Cosign, Trivy, Python — with one-line rationale each, under 200 words total)
- Structure mirrors `Agentic_DevOps/README.md`

### 12.2 `NFCU-session-1/LAB_GUIDE.md`
Attendee post-webinar walkthrough. Opens with **Prerequisites** section listing: AWS sandbox account, lab-platform-iac applied, `AWS_ROLE_ARN` repo variable set, three GitHub Environments created. Links to `lab-platform-iac/README.md` for sandbox setup.

Then four numbered lab segments, each ending in a "Success criterion" bullet:
1. **Validation** — push trivial commit, see green; push with `model_version = "latest"`, see red with specific log line; revert.
2. **Container build/sign** — flip `ENABLE_CONTAINER_STAGE` to `"true"`; watch full pipeline; verify image + signature in ECR; verify digest match.
3. **Dev deploy** — `terraform plan` review, apply, watch endpoint provision (~4–6 min), invoke with sample payload, verify response.
4. **Prod promote** — open promote PR; merge; manually trigger production workflow with `change_ticket_reference=LAB-001`; approve at the gate; verify endpoint live; verify audit trail entry has all 15 fields including `schema_version: 1`.

### 12.3 `NFCU-session-1/FAQ.md`
Nine answers, in this order, each at most 200 words:

1. Why GitHub Actions and not Jenkins/GitLab/CircleCI?
2. Why Terraform and not CDK or Pulumi?
3. How does this work for HuggingFace models?
4. What if our model registry is MLflow, not Unity Catalog or SageMaker Model Registry?
5. How do you handle model dependencies that conflict across models?
6. Can I skip the staging environment for low-risk models?
7. How long does this scale to? 1000 models?
8. What's the cost overhead of all this audit machinery?
9. Does this satisfy SR 11-7?

### 12.4 `NFCU-session-1/session-outline.md`
Public-safe version of Michael's speaker outline. Slide-by-slide structure preserved from the internal NFCU session-1 source doc. **Body text must not contain `NFCU`, `Navy Federal`, `credit union`, or `member`** — replace with "regulated FS", "users", "customers" as appropriate. (Note: the folder name `NFCU-session-1/` is the stable identifier and stays. This requirement is about content, not paths.) Verification step: `grep -i 'nfcu\|navy federal\|credit union\|\bmember\b' NFCU-session-1/session-outline.md` returns no matches.

### 12.5 `NFCU-session-1/docs/reference-card.md`
One printed page. Sections:
- Five non-negotiables (traceability, no long-lived creds, artifacts stay in VPC, prod requires approval, rollback is one click)
- The four-stage pipeline diagram (text)
- The five-minute test statement
- Three Monday actions

Must render to exactly one page when converted via `pandoc` with default settings at letter size.

### 12.6 `NFCU-session-1/docs/security-pinning.md`
Documents:
- The March 19, 2026 supply chain compromise: `aquasecurity/trivy-action` (75 of 76 version tags force-pushed to malicious commits), `aquasecurity/setup-trivy` (all 7 tags), poisoned binaries `v0.69.4`, `v0.69.5`, `v0.69.6`
- The mitigation: pin all third-party actions by full 40-char commit SHA
- Side-by-side bad/good examples for at least three actions
- How to look up the SHA for a tag: `git ls-remote https://github.com/<owner>/<repo>`

### 12.7 `NFCU-session-1/docs/cross-session-continuity.md`
Three sections — Session 2 (champion-challenger, June 4), Session 3 (monitoring, June 16), Session 4 (KServe migration, June 18). Each section lists what Session 1 artifacts the downstream session reuses (endpoint ARN, model package ARN, audit bucket location, training run ID format, audit `schema_version`). Each flags preservation requirements (e.g., "don't delete the Session 1 endpoint if you plan to attend Session 2").

Plus a numbered "Five-minute trace procedure" — each step a single CLI command with expected output format shown.

### 12.8 `NFCU-session-1/resources.md`
Annotated reading list. Required entries:
- SR 11-7 (Fed model risk management)
- FFIEC IT examination handbook
- NCUA (credit union supervisory references)
- OWASP LLM Top 10 (November 2025 revision, LLM03 Supply Chain, LLM04 Data and Model Poisoning)
- SLSA framework (target: level 3)
- CycloneDX ML-BOM (v1.5+)
- OWASP AIBOM Project (2025)
- EU AI Act Digital Omnibus political agreement (May 7, 2026) — high-risk obligations deferred to December 2027 / August 2028
- Treasury FS AI Risk Management Framework
- Colorado AI Act

---

## 13. Modifications to existing files

### 13.1 Root `README.md`
Add a `### [NFCU Session 1: ML Deployment Pipelines](NFCU-session-1/)` section to the Available Content list, parallel in structure and length to the existing `### [Agentic DevOps](Agentic_DevOps/)` section. No other content modified.

### 13.2 Root `CLAUDE.md`
Currently says `Stack: Documentation / Markdown`. Update to note Terraform, Python, Bash, and GitHub Actions are now in scope under `NFCU-session-*/` directories. Preserve the markdown reference for the existing collateral.

### 13.3 Root `.gitignore`
Add:
- Python: `__pycache__/`, `*.pyc`, `.venv/`, `*.egg-info/`
- Terraform: `.terraform/`, `*.tfstate`, `*.tfstate.backup`, `*.tfvars` with `!*.tfvars.example` exception
- Preserve all existing patterns

---

## 14. Stub session directories

`NFCU-session-2/`, `NFCU-session-3/`, `NFCU-session-4/` each contain a single `README.md`:

```markdown
# NFCU Session N: <title>

**Planned delivery date**: <date from the series schedule>

Content lands here closer to the session date. See [NFCU-session-1/](../NFCU-session-1/) for the foundation this session builds on.
```

Session titles and dates:
- Session 2 (June 4, 2026): Champion-Challenger Deployment Patterns
- Session 3 (June 16, 2026): Monitoring, Drift Detection & Observability
- Session 4 (June 18, 2026): Kubernetes-Native Model Serving with KServe

---

## 15. Verification — run before declaring done

```bash
# Formatting and structural
terraform fmt -recursive NFCU-session-1/terraform/
terraform fmt -recursive NFCU-session-1/lab-platform-iac/
# (no diffs expected)

# Terraform validation
for d in NFCU-session-1/terraform/environments/{dev,staging,production} NFCU-session-1/lab-platform-iac; do
  (cd "$d" && terraform init -backend=false && terraform validate)
done

# Python
python -m py_compile NFCU-session-1/pipeline/*.py NFCU-session-1/scripts/*.py

# Shell
shellcheck NFCU-session-1/pipeline/*.sh

# Workflows
actionlint .github/workflows/nfcu-session-1-*.yml
yamllint .github/workflows/nfcu-session-1-*.yml

# Training script dry-run
python NFCU-session-1/scripts/train-sample-model.py --dry-run

# Determinism: two consecutive real runs produce same tarball SHA256
python NFCU-session-1/scripts/train-sample-model.py && mv model-v1.0.0.tar.gz /tmp/run1.tar.gz
python NFCU-session-1/scripts/train-sample-model.py && mv model-v1.0.0.tar.gz /tmp/run2.tar.gz
[ "$(sha256sum /tmp/run1.tar.gz | cut -d' ' -f1)" = "$(sha256sum /tmp/run2.tar.gz | cut -d' ' -f1)" ] || echo "DETERMINISM CHECK FAILED"

# validate.py rejects each mutable identifier
for v in latest prod current stable main Latest PROD; do
  python NFCU-session-1/pipeline/validate.py --artifact file:///tmp/run1.tar.gz --model-version "$v"
  [ $? -eq 2 ] || echo "FAILED to reject $v"
done

# Secrets scan
gitleaks detect --source . --no-banner

# Third-party action SHA pinning enforcement
# (Expected: only matches under actions/, aws-actions/, github/ namespaces)
grep -rE 'uses: [^@]+@[^a-f0-9]' .github/workflows/nfcu-session-1-*.yml | \
  grep -v 'actions/\|aws-actions/\|github/' && echo "UNPINNED THIRD-PARTY ACTIONS FOUND" || echo "SHA pinning OK"

# No NFCU references in public session-outline body
grep -i 'nfcu\|navy federal\|credit union\|\bmember\b' NFCU-session-1/session-outline.md && echo "NFCU LEAK" || echo "Outline scrubbed"

# No tfvars committed (only .example)
git ls-files | grep -E '\.tfvars$' && echo "REAL TFVARS COMMITTED" || echo "OK"
```

All checks must pass before the commit is final.

---

## 16. Definition of done

- [ ] All sections 1–15 implemented.
- [ ] All checks in §15 pass.
- [ ] Repo tree under `NFCU-session-1/` exactly matches §2.2.
- [ ] Workflow files at `.github/workflows/` exactly match §2.3.
- [ ] No file under `Agentic_DevOps/` modified.
- [ ] No real secrets in any committed file (gitleaks clean).
- [ ] Final commit message: `feat(nfcu-session-1): bootstrap deployment pipeline for live demo webinar`.
- [ ] Tag the commit `nfcu-session-1-v1.0.0`.
- [ ] PR description copied from §1, §2.1, §2.2, §2.3 of this spec.
