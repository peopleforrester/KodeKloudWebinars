# Design

## 4.1 Architectural Approach

The lab implements shadow deployment via a **Lambda / API Gateway fan-out** pattern. Three alternative patterns are discussed in the speaker content (SageMaker Shadow Variants, Istio mirror / Seldon Core shadow predictor, Lambda fan-out). The fan-out is selected because:

1. **Portability** — same pattern works against SageMaker, ECS, on-prem Kubernetes, any HTTP-serving inference backend
2. **Pedagogical transparency** — comparison logic is explicit and inspectable; nothing hidden inside a managed feature
3. **Cross-environment teaching** — attendees take home a pattern that doesn't require a specific cloud feature

This choice MUST be documented in `MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/docs/why-lambda-fanout.md` so attendees do not leave thinking SageMaker can't do native shadow. It can (ShadowProductionVariants, GA re:Invent 2022) — the lab just doesn't use it.

## 4.2 Data Flow

```
caller → API Gateway → shadow-mirror Lambda
                              │
                              ├─► champion SageMaker endpoint  ──► response → caller
                              │
                              └─► challenger SageMaker endpoint ──► response → S3 (shadow-logs)
                                                                       │
                                                                       ▼
                                       EventBridge (5-min schedule) → comparison Lambda
                                                                       │
                                                                       ├─► CloudWatch custom metrics
                                                                       └─► S3 (comparison-results)
                                                                                 │
                                                                                 ▼
                                                        session-2-promote-challenger.yml reads latest
                                                                                 │
                                                                                 ▼
                                                        criteria evaluated against promotion-criteria.yaml
                                                                                 │
                                                                                 ├─► fail: workflow refuses to flip
                                                                                 └─► pass: workflow updates shadow-mirror
                                                                                          env vars + writes audit entry
```

## 4.3 Key Architectural Decisions

### Decision: First runnable webinar in a previously collateral-only repo

**Decision:** Add Python, Terraform, GitHub Actions tooling to a repo that has been documentation-only. Configure all runnable-code tooling to exclude `Agentic_DevOps/` and any future collateral-only webinar directories.

**Rationale:** Single source of truth for KodeKloud webinar content. Avoids the alternative pain of a sibling runnable-only repo that drifts from the collateral repo.

**Implication for CI:** Every linter, scanner, and test runner MUST scope itself by path. Patterns to apply:
- pre-commit: `exclude: ^Agentic_DevOps/`
- ruff: `extend-exclude = ["Agentic_DevOps"]`
- mypy: explicit `files = ["MLOps_Deployment_Workshop/**/lambdas/**", ...]`
- terraform / tflint / tfsec / Checkov: only run against discovered Terraform paths under `MLOps_Deployment_Workshop/` and `shared/`
- GitHub Actions `paths:` filters: never include `Agentic_DevOps/**`

### Decision: Single root-level OpenSpec, sessions as bounded contexts

**Decision:** One `openspec/` directory at the repo root governs all sessions and all webinars. Capabilities are named at the conceptual level (`shadow-deployment`, `model-comparison`) rather than scoped to sessions.

**Rationale:** OpenSpec's strength is treating specs as a durable source of truth. If Session 3 introduces a `model-monitoring` capability that builds on `model-comparison`, it can MODIFY the existing capability rather than create a parallel one. Session boundaries are documentation/organizational, not capability boundaries.

### Decision: Workflows at repo root, path-filtered to Session 2

**Decision:** Session 2 workflows live at `.github/workflows/session-2-*.yml`. Each workflow uses `paths:` filters and a `working-directory:` default so it only fires when Session 2 files change.

**Rationale:** GitHub Actions requires workflows at `.github/workflows/` at the repo root. Filename prefix + path filters provide the scoping.

```yaml
# Example header for session-2-deploy-challenger.yml
on:
  workflow_dispatch:
    inputs:
      attendee_id:
        required: true
  push:
    branches: [main]
    paths:
      - 'MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/**'
      - 'shared/terraform-modules/audit_trail/**'
      - '.github/workflows/session-2-deploy-challenger.yml'
defaults:
  run:
    working-directory: MLOps_Deployment_Workshop/Session_2_Shadow_Deployment
```

### Decision: Lambda env-var swap as the "traffic flip" mechanism

**Decision:** The promotion workflow flips traffic by updating two environment variables on the `shadow-mirror-{attendee-id}` Lambda: `CHAMPION_ENDPOINT_ARN` and `CHALLENGER_ENDPOINT_ARN`.

**Rationale:** Pedagogically clean. Attendees can read the Lambda config and see what changed. One API call. Reversible.

**Production equivalents to call out in `docs/architecture.md`:** weighted DNS records, service mesh routes (Istio VirtualService weights), feature flag services (LaunchDarkly), or SageMaker's native `update-endpoint` with `promote-shadow-variant`. The lab's mechanism is illustrative, not recommended for production routing state.

### Decision: Async challenger invocation, sync champion invocation

**Decision:** In the shadow-mirror Lambda, champion is invoked synchronously (response returned to caller). Challenger is invoked via `boto3` SageMaker `InvokeEndpointAsync` so caller latency is not affected by challenger latency.

**Rationale:** Preserves the "zero member impact" property even when the challenger is slow or fails. A failing challenger must never cause caller-visible degradation.

**Implication for comparison logic:** Challenger responses arrive in S3 from SageMaker's async output location. The comparison Lambda joins on a `request_id` UUID written by the shadow-mirror.

### Decision: Auto-approval bot for the promotion workflow

**Decision:** A `workshop-approver-bot` GitHub App auto-approves the promotion workflow's required review.

**Rationale:** Live workshop time budget cannot accommodate a multi-person human review loop. The pattern teaches **that** promotion is a multi-reviewer calendared event; the lab's auto-approval is a stand-in.

**Required callout in `LAB_GUIDE.md`:** "In production this is a calendared event with model owner, model validator, deploying engineer, and risk officer all signing off. The auto-approval bot in this lab is a stand-in for that human loop."

### Decision: ~92% agreement rate is engineered, not emergent

**Decision:** The challenger (`model-v1.0.1`) is trained with hyperparameters specifically chosen to produce ~92% agreement with the champion on the UCI Adult test split (`max_depth=8, n_estimators=150` versus champion's `max_depth=6, n_estimators=100`). The traffic generator additionally biases ~15% of samples toward the pre-identified disagreement region.

**Rationale:** Workshop pedagogy. 99% agreement → boring. 50% agreement → unrealistic. ~92% gives attendees a meaningful comparison without a 2-week shadow run.

**Validation requirement:** The lab-engineer dry-run on or before May 30, 2026 must confirm the agreement rate lands in 90–94%. If it doesn't, retrain `model-v1.0.1` with adjusted hyperparameters.

### Decision: UCI Adult dataset, with disparate-impact caveat

**Decision:** UCI Adult Census Income dataset is used for both training and the synthetic traffic stream.

**Caveat (MUST appear in `LAB_GUIDE.md` and Slide 12 speaker notes):** UCI Adult's protected-class fields (sex, race) are binary and limited. Real-world fair lending analysis works with richer demographic features and more nuanced subgroup definitions. The lab's specific disparate-impact numbers are not representative of production.

### Decision: Ground truth available immediately (lab simplification)

**Caveat (MUST appear in `LAB_GUIDE.md` and Slide 13 speaker notes):** UCI Adult includes labels, so accuracy delta is computable immediately. In real credit modeling, default outcomes take 12–24 months to materialize. Proxy signals (agreement rate, prediction distribution stability, downstream operational metrics) do most of the heavy lifting in production shadow runs. The lab cannot teach this directly; it must be flagged.

## 4.4 Per-Attendee Provisioning Model

Each of the 25–30 attendees gets:

- A SageMaker challenger endpoint: `workshop-lab-{attendee-id}-challenger`
- Three Lambda functions: `shadow-mirror-{attendee-id}`, `comparison-{attendee-id}`, `traffic-generator-{attendee-id}`
- Two S3 buckets: `workshop-lab-{attendee-id}-shadow-logs`, `workshop-lab-{attendee-id}-comparison-results`
- One CloudWatch dashboard: `workshop-lab-{attendee-id}-shadow`
- One EventBridge rule (5-min schedule on the comparison Lambda)
- IAM permissions on existing role (from Session 1): invoke both endpoints, write to the two buckets, PutMetricData on CloudWatch

Provisioning runs from `MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/terraform/` parameterized on `attendee_id`. Pre-provisioning deadline: **May 25, 2026** (10 business days before session).

## 4.5 Cost Model

| Item | Estimate |
|---|---|
| Per-attendee, active lab (2× ml.m5.xlarge endpoints @ ~2.5h + Lambda + S3 + CloudWatch) | $1.50–$2.50 |
| Per-attendee, June 4 → June 16 carry (1× ml.m5.xlarge held InService for Session 3) | ~$55–$80 |
| Total active lab, 30 attendees | $45–$75 |
| Total carry, 30 attendees | ~$1,650–$2,400 |

All figures sourced from the Session 2 v1.3 lab engineer reference card. FinOps must confirm before commit if sandbox accounts have negotiated rates.

## 4.6 Local Validation Strategy

**Root-level** `scripts/validate-local.sh` discovers session-specific validators and runs them, then runs cross-cutting checks that NEVER touch `Agentic_DevOps/`:

```bash
#!/usr/bin/env bash
set -euo pipefail
for session_validator in MLOps_Deployment_Workshop/Session_*/scripts/validate-session-*.sh; do
  echo "==> Running $session_validator"
  bash "$session_validator"
done
echo "==> Cross-cutting checks (excluding Agentic_DevOps/)"
ruff check . --extend-exclude Agentic_DevOps
ruff format --check . --extend-exclude Agentic_DevOps
mypy --strict MLOps_Deployment_Workshop/*/lambdas/
pytest --cov=MLOps_Deployment_Workshop
```

**Per-session** `MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/scripts/validate-session-2.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."   # cd into Session_2_Shadow_Deployment/
terraform -chdir=terraform fmt -check -recursive
terraform -chdir=terraform validate
tflint --chdir=terraform
tfsec terraform/
checkov -d terraform/ --quiet
kics scan -p terraform/ --report-formats json -o /tmp/kics-s2
ruff check lambdas/ models/ tests/
mypy --strict lambdas/
pytest tests/
python models/train_champion.py --dry-run
python models/train_challenger.py --dry-run
```

Both wired into `.pre-commit-config.yaml` with `exclude: ^Agentic_DevOps/`. CI runs the same chain.
