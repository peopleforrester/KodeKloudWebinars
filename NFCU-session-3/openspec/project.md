# Project Context — NFCU Session 3

## Purpose

NFCU Session 3 of the MLOps Learning Sessions: a 2-hour live workshop on
monitoring deployed ML models, detecting drift, integrating Evidently AI and
NannyML, and executing runbooks against simulated production incidents. Supports
up to 30 concurrent attendees in per-attendee AWS sandboxes.

The driving idea: traditional infrastructure monitoring does not catch the
"silent wrongness" failure mode — a model returning HTTP 200 with low latency
while producing wrong predictions for weeks. Every artifact targets that failure
class.

## Stack

- **Compute:** AWS Lambda (Python 3.11) — zip packages (drift-detector,
  drift-simulator, incident-simulator) and container images (evidently-runner,
  nannyml-runner).
- **Monitoring:** CloudWatch (custom metrics, dashboard, alarms), SNS (visible,
  non-paging), EventBridge (2-min schedule).
- **Model serving:** SageMaker real-time endpoint (UCI Adult binary classifier,
  carried from Sessions 1/2).
- **IaC:** Terraform ≥ 1.6. **Region:** us-east-1.
- **Drift libraries:** Evidently 0.7.x, NannyML (CBPE).

## Conventions

- This OpenSpec lives at `NFCU-session-3/openspec/` (per-session, not repo-root).
- Change folders are named for the capability (`monitoring`).
- Shared assets are **session-local** under `NFCU-session-3/shared/` — Session 3
  ships its own baseline model + fixtures and does not depend on Sessions 1/2/4
  being built.
- Touch boundary: only `NFCU-session-3/**`. (The deploy workflow is nested at
  `NFCU-session-3/.github/workflows/` rather than the repo root per the build
  owner's "everything nested" directive; see `../RUN_CONFIG.md`.)
- No fabricated regulatory claims (D12): monitoring patterns *align with* model
  risk principles but are not a compliance attestation; never call NFCU a "bank".

## Active change

- `changes/monitoring/` — the Session 3 lab build (this change).
