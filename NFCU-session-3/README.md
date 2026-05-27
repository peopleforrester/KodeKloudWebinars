# NFCU Session 3 — Keeping 100+ Models Healthy

Practitioner collateral and lab environment for **MLOps Learning Session 3**, a
2-hour live workshop on monitoring deployed ML models. The session exists because
traditional infrastructure monitoring does not catch the failure mode that hurts
most in production: a model returning HTTP 200 with low latency while producing
**wrong predictions** for weeks. Everything here is built to detect that.

The lab runs against a SageMaker endpoint (a UCI Adult income classifier carried
from Sessions 1/2) in a per-attendee AWS sandbox, and layers on drift detection,
drift reporting, performance estimation, and simulated incidents with runbooks.

> **Self-contained:** everything needed to build, test, and validate this lab
> lives in **this directory**. Every command below is run from inside
> `NFCU-session-3/`. Nothing depends on the repository root or on the other
> `NFCU-session-*/` directories.

---

## What's Here

| Folder | What it contains | Who it's for |
|--------|-----------------|--------------|
| [lambdas/](lambdas/) | Five Lambda functions: drift-detector (PSI), drift-simulator, evidently-runner, nannyml-runner, incident-simulator | Lab engineers deploying the lab |
| [monitoring/](monitoring/) | CloudWatch dashboard (2 rows: infra + ML) and the three production alarms | Lab engineers; attendees in Lab 1 |
| [infra/](infra/) | Terraform for per-attendee S3 buckets, IAM, and the EventBridge schedule | Lab engineers provisioning sandboxes |
| [runbooks/](runbooks/) | A 5-phase runbook template plus five incident-specific runbooks | Attendees in Lab 4; reusable by NFCU on-call |
| [scripts/](scripts/) | Reference capture, baseline-model build, endpoint restore, lab-readiness | Lab engineers and assistants pre-session |
| [shared/](shared/) | Session-local baseline model artifact and UCI Adult fixtures | The restore script and the simulators |
| [tests/](tests/) | Unit + moto-mocked integration tests, and dry-run result docs | Anyone validating the build |
| [openspec/](openspec/) | The OpenSpec change (`monitoring`) that specifies this build | Reviewers and the next session |
| [LAB_GUIDE.md](LAB_GUIDE.md) | Per-attendee provisioning runbook and per-lab timing | Lab engineers running the session |
| [LAB_ASSISTANT_BRIEFING.md](LAB_ASSISTANT_BRIEFING.md) | Pre-flight protocol and session-day briefing | The 2 lab assistants |
| [RUN_CONFIG.md](RUN_CONFIG.md) | Build decisions, toolchain, and what is deferred | Anyone integrating or auditing |

---

## Prerequisites

| Tool | Needed for | Notes |
|------|-----------|-------|
| Python **3.11+** | Lambdas, tests, scripts | Lambda runtime is 3.11; local dev works on 3.11–3.13 |
| [`uv`](https://docs.astral.sh/uv/) **or** `pip`+`venv` | environment setup | `uv` preferred |
| Terraform **≥ 1.6** | `terraform validate` on `infra/` and `monitoring/` | apply needs a sandbox |
| AWS CLI v2 + sandbox creds | live deploy / dry-run only | not needed for tests or validate |
| Docker | building the evidently/nannyml images | container Lambdas only |
| `actionlint`, `shellcheck` | linting the workflow and shell scripts | optional |

All Python dev dependencies (boto3, pandas, pyarrow, numpy, scipy, pytest,
moto, scikit-learn, joblib) are declared in [`pyproject.toml`](pyproject.toml)
under the `dev` extra.

---

## Set Up and Run Locally

From inside `NFCU-session-3/`:

```bash
# --- with uv (preferred) ---
uv venv
uv pip install -e ".[dev]"
uv run pytest                 # 22 tests, moto-mocked AWS — no live account needed

# --- or with pip + venv ---
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

### Regenerate the reference distribution (built once at lab-build time)

```bash
uv run python scripts/capture-reference-distribution.py
# -> reference.parquet  (15,315 rows x 8 features, from shared/fixtures/uci-adult/)
```

### Rebuild the baseline model artifact (recovery stand-in)

```bash
uv run python scripts/build-baseline-model.py
# -> shared/baseline-models/session-1-2-uci-adult/model.tar.gz  (SageMaker sklearn artifact)
```

### Validate the infrastructure as code

```bash
terraform -chdir=infra       init -backend=false && terraform -chdir=infra       validate
terraform -chdir=monitoring  init -backend=false && terraform -chdir=monitoring  validate
```

### Lint the workflow and scripts (optional)

```bash
actionlint .github/workflows/nfcu-session-3-deploy-monitoring.yml
shellcheck scripts/*.sh
```

Running all of the above clean is the full local acceptance bar. What it does
**not** cover — live AWS provisioning, Docker image builds, browser rendering of
the Evidently report, and the date-gated Evidently/NannyML pin re-verification —
is documented and tracked in [tests/dry_run_results.md](tests/dry_run_results.md)
and [RUN_CONFIG.md](RUN_CONFIG.md).

---

## Deploy to a Sandbox (live)

Provisioning a per-attendee sandbox needs AWS credentials and is covered
step-by-step in the [Lab Guide](LAB_GUIDE.md#per-attendee-provisioning). In short,
from inside `NFCU-session-3/`:

```bash
# infra (buckets, IAM, five Lambdas, EventBridge schedule)
terraform -chdir=infra apply -var="attendee_id=lab-007" -var="region=us-east-1"
# monitoring (three alarms + SNS)
terraform -chdir=monitoring apply -var="attendee_id=lab-007"
# dashboard
sed 's/{attendee_id}/lab-007/g' monitoring/dashboard.json > /tmp/dash.json
aws cloudwatch put-dashboard --dashboard-name workshop-lab-lab-007 --dashboard-body file:///tmp/dash.json
```

Pre-session, verify all sandboxes and restore any that are down:

```bash
scripts/verify-lab-readiness.sh --cohort cohort.txt
scripts/restore-session2-endpoint.sh --attendee-id lab-007   # idempotent, <=4 min
```

---

## Start Here (by role)

**"I'm a lab engineer setting up the sandboxes for session day."**
Go to the [Lab Guide](LAB_GUIDE.md) for the per-attendee provisioning runbook
(≤ 15 min/attendee) and the pre-flight protocol, then
[LAB_ASSISTANT_BRIEFING.md](LAB_ASSISTANT_BRIEFING.md).

**"I'm an attendee and I want to understand what I'm about to build."**
The flow: **Lab 1** instruments the endpoint and stands up the dashboard + alarms;
**Lab 2** injects drift and watches the PSI alarm fire; **Lab 3** runs the
Evidently report and the NannyML performance estimate; **Lab 4** triggers a
simulated incident and routes it with a [runbook](runbooks/). Read the
[runbook template](runbooks/runbook-template.md) first so the routing rule is in
your head before the incident hits.

**"I'm reviewing this build for correctness or for NFCU."**
Start with the [OpenSpec proposal](openspec/changes/monitoring/proposal.md) and
[design.md](openspec/changes/monitoring/design.md) (decisions D1–D12). The
[spec deltas](openspec/changes/monitoring/specs/) are EARS-format requirements;
every scenario is demonstrable. Note D12: this material *aligns with* model-risk
principles but makes **no** regulatory compliance claim.

---

## Lab 1 Setup (the 60-second version)

1. Confirm your Session 1/2 endpoint is `InService` (the lab assistant runs
   `scripts/verify-lab-readiness.sh`; if red, they run
   `scripts/restore-session2-endpoint.sh`).
2. Apply the dashboard and alarms for your `attendee_id` — see
   [LAB_GUIDE.md → Per-Attendee Provisioning](LAB_GUIDE.md#per-attendee-provisioning).
3. Open the CloudWatch dashboard. Confirm the top (infrastructure) row populates.
4. You're ready for Lab 2.

---

See [resources.md](resources.md) for the external reading list.
