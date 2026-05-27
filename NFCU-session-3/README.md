# NFCU Session 3 — Keeping 100+ Models Healthy

Practitioner collateral and lab environment for **MLOps Learning Session 3**, a
2-hour live workshop on monitoring deployed ML models. The session exists because
traditional infrastructure monitoring does not catch the failure mode that hurts
most in production: a model returning HTTP 200 with low latency while producing
**wrong predictions** for weeks. Everything here is built to detect that.

The lab runs against a SageMaker endpoint (a UCI Adult income classifier carried
from Sessions 1/2) in a per-attendee AWS sandbox, and layers on drift detection,
drift reporting, performance estimation, and simulated incidents with runbooks.

---

## What's Here

| Folder | What it contains | Who it's for |
|--------|-----------------|--------------|
| [lambdas/](lambdas/) | Five Lambda functions: drift-detector (PSI), drift-simulator, evidently-runner, nannyml-runner, incident-simulator | Lab engineers deploying the lab |
| [monitoring/](monitoring/) | CloudWatch dashboard (2 rows: infra + ML) and the three production alarms | Lab engineers; attendees in Lab 1 |
| [infra/](infra/) | Terraform for per-attendee S3 buckets, IAM, and the EventBridge schedule | Lab engineers provisioning sandboxes |
| [runbooks/](runbooks/) | A 5-phase runbook template plus five incident-specific runbooks | Attendees in Lab 4; reusable by NFCU on-call |
| [scripts/](scripts/) | Endpoint restore, reference-distribution capture, and lab-readiness verification | Lab engineers and assistants pre-session |
| [shared/](shared/) | Session-local baseline model artifact and UCI Adult fixtures | The restore script and the simulators |
| [tests/](tests/) | Unit + moto-mocked integration tests, and dry-run result docs | Anyone validating the build |
| [openspec/](openspec/) | The OpenSpec change (`monitoring`) that specifies this build | Reviewers and the next session |
| [LAB_GUIDE.md](LAB_GUIDE.md) | Lab engineer reference: provisioning runbook and per-lab timing | Lab engineers running the session |

---

## Start Here

**"I'm a lab engineer setting up the sandboxes for session day."**
Go straight to the [Lab Guide](LAB_GUIDE.md). It has the per-attendee provisioning
runbook (target: ≤ 15 min per attendee) and the pre-flight protocol. Before the
session, run [`scripts/verify-lab-readiness.sh`](scripts/verify-lab-readiness.sh)
across all 30 attendees and restore any red sandbox with
[`scripts/restore-session2-endpoint.sh`](scripts/restore-session2-endpoint.sh).

**"I'm an attendee and I want to understand what I'm about to build."**
The flow is: **Lab 1** instruments the endpoint and stands up the dashboard +
alarms; **Lab 2** injects drift and watches the PSI alarm fire; **Lab 3** runs the
Evidently report and the NannyML performance estimate; **Lab 4** triggers a
simulated incident and routes it using a [runbook](runbooks/). Start by reading
the [runbook template](runbooks/runbook-template.md) so the routing rule is in
your head before the incident hits.

**"I'm reviewing this build for correctness or for NFCU."**
Start with the [OpenSpec change](openspec/changes/monitoring/proposal.md) for
intent and scope, then [design.md](openspec/changes/monitoring/design.md) for the
decisions (D1–D12). The [spec deltas](openspec/changes/monitoring/specs/) are
EARS-format requirements; every scenario is meant to be demonstrable. Note D12:
this material *aligns with* model-risk principles but makes **no** regulatory
compliance claim.

---

## Lab 1 Setup (the 60-second version)

1. Confirm your Session 1/2 endpoint is `InService` (the lab assistant runs
   `verify-lab-readiness.sh`; if red, they run `restore-session2-endpoint.sh`).
2. Apply the dashboard and alarms for your `attendee_id` — see
   [LAB_GUIDE.md → Per-Attendee Provisioning](LAB_GUIDE.md#per-attendee-provisioning).
3. Open the CloudWatch dashboard. Confirm the top (infrastructure) row populates.
4. You're ready for Lab 2.

---

## How to Use This Repo

The code targets the AWS Lambda Python 3.11 runtime. Tests run locally with
`pytest` against moto-mocked AWS (no live account needed) — see
[tests/](tests/). Terraform under `monitoring/` and `infra/` is validated with
`terraform validate`; applying it requires a lab sandbox.

See [resources.md](resources.md) for the external reading list and
[`../RUN_CONFIG.md`](../RUN_CONFIG.md) for build-environment notes.
