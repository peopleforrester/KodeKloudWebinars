# Run Configuration — `monitoring` (NFCU Session 3)

Adapter notes for executing `OPENSPEC_CHANGE_monitoring.md` in this repo.
The spec is the authoritative source; this file records execution decisions and
environment realities that the spec does not.

## Authoritative spec

`NFCU-session-3/OPENSPEC_CHANGE_monitoring.md` (the NFCU version). The earlier
placeholder `OPENSPEC_CHANGE_session-3-monitoring.md` (repo `ml-deploy-workshop`)
was superseded and deleted.

## Build root: EVERYTHING nested in `NFCU-session-3/`

Per Michael's directive ("Everything needs to be nested in NFCU session three.
Everything." + "do not touch anything else"), there are **zero** writes outside
`NFCU-session-3/`.

### Override of spec §2 / D11 (workflow location)

The spec places the GitHub Actions workflow at the repo-root `.github/workflows/`
as its one stated exception. **This is overridden.** The workflow is created at:

    NFCU-session-3/.github/workflows/nfcu-session-3-deploy-monitoring.yml

**Consequence (accepted):** GitHub Actions only reads workflows from the
repo-root `.github/`, so this file will NOT run as live CI. That is acceptable —
this repo is archived webinar collateral; the workflow is illustrative and
self-contained, not a live pipeline. Recorded so no one "fixes" it by moving it
to the repo root, which would violate the touch boundary.

## Branch (shared-worktree caveat)

This working tree is shared by parallel agents building NFCU sessions 1–4. HEAD
moved between branches mid-build, so all commits landed interleaved on one branch
line (current tip = the Phase 9/10 work). The `feat/nfcu-session-3-monitoring`
ref never advanced past the base. Every NFCU-session-3 commit was scoped to
`NFCU-session-3/` only (verified per commit). Not pushed; no commits to `main`.
Michael should reconcile branches before any push — do not untangle destructively.

## Local toolchain (what "verified" means here)

| Capability | Status | Used for |
|---|---|---|
| python3.13 venv + pandas/numpy/pyarrow/boto3/moto/scipy/pytest | ✅ in `.venv/` | unit + moto integration tests |
| terraform 1.15.4 | ✅ | `terraform validate` on .tf |
| actionlint 1.7.12 | ✅ | workflow lint |
| docker 29.5.2 | ✅ present | Dockerfiles authored; image builds heavy/deferred |
| aws cli 2.34 | ✅ present, NO live creds/account | cannot provision/plan against AWS |

## Acceptance criteria that CANNOT execute in this environment

These are authored to spec and marked **deferred** in the dry-run docs — never
reported as passed:

- **4.1 / 5.1 pin re-verification** — date-gated to ≥ June 9, 2026. Today is
  May 27. Pins set to spec values now; re-verify task remains open.
- **Live AWS**: `terraform plan/apply`, 30-sandbox provisioning, real endpoint
  invocation, restore-script ≤4 min wall-clock, CloudWatch dashboard render.
- **Docker image size** (<1.5 GB compressed) — requires building against
  `public.ecr.aws/lambda/python:3.11`.
- **Browser screenshots** of the Evidently HTML report.
- **Real-data timing/AUC delta** (Lab 2 PSI<5min, NannyML delta>0.01).

## Status

Spec ingested. Build in progress on `feat/nfcu-session-3-monitoring`.
See `PROJECT_STATE.md` for phase-by-phase progress.
