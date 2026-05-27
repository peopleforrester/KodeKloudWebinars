# Proposal — `monitoring` (NFCU Session 3)

> Split from `NFCU-session-3/OPENSPEC_CHANGE_monitoring.md` §1. That combined
> document remains the authoritative source.

## Intent

Build the complete lab environment for NFCU Session 3 of the MLOps Learning
Sessions: a 2-hour live workshop on monitoring deployed ML models, detecting
drift across three drift types, integrating Evidently AI and NannyML, and
executing runbooks against simulated production incidents. The lab supports up
to 30 concurrent attendees in a per-attendee AWS sandbox.

The session exists because traditional infrastructure monitoring does not catch
the "silent wrongness" failure mode — a model returning HTTP 200 with
sub-millisecond latency while producing wrong predictions for weeks. Every
artifact in this build strengthens an attendee's ability to detect that class of
failure.

## What's changing

This change builds the `NFCU-session-3/` subtree inside the existing
`KodeKloudWebinars` repo:

- All Session 3 source under `NFCU-session-3/` (Lambdas, monitoring, infra,
  runbooks, scripts, tests, session-local shared assets, and OpenSpec).
- A session-scoped GitHub Actions workflow at
  `NFCU-session-3/.github/workflows/nfcu-session-3-deploy-monitoring.yml`.

> **Build-owner override:** the authoritative spec §2/D11 places the workflow at
> the repo-root `.github/workflows/`. For this build everything is nested under
> `NFCU-session-3/`, so the workflow lives at `NFCU-session-3/.github/workflows/`.
> See `../../../RUN_CONFIG.md`.

No code outside `NFCU-session-3/**` is modified. The existing `Agentic_DevOps/`
content is untouched. Sessions 1, 2, and 4 (when they land) sit as peers; this
change does not assume they exist.

After this change the repo contains executable code (Python Lambdas, Dockerfiles,
Terraform, shell scripts) for the first time. The repo-root `CLAUDE.md` "Stack:
Documentation / Markdown" line should be updated, but that is governed by a
separate change.

## Out of scope

- NFCU Sessions 1, 2, 4 builds. The Session 1/2 SageMaker endpoint is an external
  dependency; `scripts/restore-session2-endpoint.sh` recovers it. The baseline
  model artifact lives in `NFCU-session-3/shared/` so Session 3 is
  self-recoverable.
- Real PagerDuty/Slack paging. SNS topics are visible but do not page.
- LLM-specific monitoring (verbal aside only).
- Long-horizon concept drift (the scenario is time-compressed; documented).
- Multi-cloud / Kubernetes (Session 4 covers KServe).
- The Session 3 slide deck (`.pptx`), authored separately.
- Updates to repo-root `README.md`, `CLAUDE.md`, `.gitignore` (separate change).

## Impact

- **Attendees:** 30 DevOps/Platform/SRE engineers leave with monitoring on a live
  endpoint, drift detection that fires, an Evidently report, a NannyML CBPE
  estimate, and a documented routing decision on a simulated incident.
- **Lab engineers:** a per-attendee pipeline costing $0.40–$0.80 per attendee.
- **NFCU stakeholders (Lovely, Keetra):** a self-contained, independently
  reviewable folder; runbook templates usable as a starting point for NFCU's own
  ML on-call rotation.
- **Series continuity:** Session 4 can reference the runbook templates and
  Evidently/NannyML patterns.

## Why now

Session is on the calendar for June 16, 2026. Lab build must be complete by
June 6 for the dry-run window. Evidently pin re-verification no later than June 9.
