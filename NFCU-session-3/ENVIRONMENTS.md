# Environments: per-attendee monitoring sandboxes

Session 3 has **no deployment ladder and no promotion flow** — it does not ship a model.
Its "environment" is a **per-attendee AWS sandbox that monitors one existing endpoint**:
the UCI Adult income classifier carried forward from Sessions 1/2. Each attendee gets
their own isolated copy of the monitoring stack pointed at their own endpoint.

## The unit of isolation: one sandbox per attendee

Each attendee sandbox provisions ([`infra/per-attendee.tf`](infra/per-attendee.tf)):

- S3 buckets for the reference dataset and drift/monitoring outputs
- IAM scoped to that attendee
- The five monitoring Lambdas — [`lambdas/`](lambdas/): PSI drift-detector, drift-simulator,
  Evidently runner, NannyML runner, incident-simulator
- An EventBridge schedule that runs the drift jobs on a cadence
- A CloudWatch dashboard + three alarms — [`monitoring/`](monitoring/)

There is no dev/staging/prod and nothing is "promoted." The model under observation is
the same endpoint from earlier sessions; Session 3 layers monitoring *around* it.

## The flow

```
existing endpoint (from S1/S2)
        │
capture reference ─▶ scheduled drift jobs (PSI / Evidently / NannyML) ─▶ dashboard + alarms
        │                                                                      │
   simulate incidents ───────────────────────────────────────────────▶ runbooks (5-phase)
```

Reference capture and baseline build run from [`scripts/`](scripts/); drift detection,
reporting, and performance estimation run on the schedule; simulated incidents exercise
the [`runbooks/`](runbooks/).

## Preserve the upstream endpoint

Session 3 assumes the Session 1/2 endpoint still exists. **Do not tear it down** if you
plan to run this lab — there is nothing for the monitoring stack to observe otherwise.

## A note on the workflow

`nfcu-session-3-deploy-monitoring.yml` (a `workflow_dispatch` job that provisions the
per-attendee infra) lives under `NFCU-session-3/.github/workflows/`, **deliberately not at
the repository root**. GitHub Actions only runs workflows from the repo root, so this one
is **illustrative and self-contained — it does not execute as live CI** (recorded in
[`RUN_CONFIG.md`](RUN_CONFIG.md) so no one "fixes" it by moving it). The Makefile/scripts
are the real entry points for building and validating the lab.
