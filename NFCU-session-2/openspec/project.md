# Project: KodeKloud Webinars Repository

## What this repo is
Practitioner collateral and (as of May 2026) runnable lab artifacts from
KodeKloud webinars. Each top-level directory is a webinar.

Webinars currently included:
- Agentic_DevOps/ — "Beyond Copilots" (April 2026); collateral-only.
- MLOps_Deployment_Workshop/ — 4-session live workshop on ML model
  deployment for DevOps engineers in regulated financial services
  (June 2026). First webinar in this repo with runnable labs.

Session schedule (MLOps_Deployment_Workshop):
- Session 1 — Deployment Pipelines (June 2, 2026)
- Session 2 — Champion-Challenger Shadow Deployments (June 4, 2026)
- Session 3 — Monitoring, Drift, and ML Runbooks (June 16, 2026)
- Session 4 — Kubernetes Model Serving (date TBD)

Sessions are sequential. Session N's outputs are inputs to Session N+1.

## Repo organization
- `<Webinar_Name>/` — all artifacts for that webinar. Collateral
  (markdown) and/or runnable code, depending on the webinar.
- `MLOps_Deployment_Workshop/Session_N_<Topic>/` — per-session
  artifacts within a multi-session webinar.
- `shared/` — utilities used by 2+ sessions. Keep small and stable.
- `.github/workflows/` — GitHub Actions workflows for ALL webinars
  (GitHub requires workflows at repo root). Workflows are scoped per
  session via filename prefix (`session-N-*.yml`) and `paths:` filters.
- `openspec/` — single OpenSpec install governing changes across all
  webinars and sessions. Each session's lab construction is its own
  change proposal.

## Convention: collateral-only vs runnable
- A webinar directory MAY be collateral-only (Agentic_DevOps/) — markdown,
  templates, slide notes; no code.
- A webinar directory MAY include runnable labs (MLOps_Deployment_Workshop/)
  — code, IaC, workflows.
- Repo-wide tooling (pre-commit, CI, linters, scanners) MUST exclude
  collateral-only webinar directories from runnable-code checks. Failure
  to do so creates fake CI failures on doc-only PRs.

## Who uses this
- Per-webinar; varies. For MLOps_Deployment_Workshop:
  25–30 DevOps Engineers, Platform Engineers, SREs, and ML Engineers per
  cohort. Audience works in regulated financial services (NCUA / FFIEC
  examined). Assume architecture and SDLC literacy; do NOT assume Python
  ML fluency.

## What this repo is NOT
- Not a production system; everything teaches patterns.
- Not a per-cloud-feature tutorial (labs deliberately use portable
  patterns like Lambda fan-out rather than cloud-native shadow features).
- Not a fair-lending compliance product (datasets are public/synthetic).

## Non-negotiables (workshop-wide)
- All sample data must be public and synthetic-safe.
- Zero NFCU data, zero NFCU-flavored synthetic data, zero proprietary
  models.
- All AWS resources tagged for cost attribution and auto-teardown.
- All Terraform must pass: tflint, tfsec, Checkov, KICS.
- No fabricated metrics in attendee-facing collateral.
- All endpoint and bucket names parameterized by attendee-id.
- Workflows MUST be path-filtered so a Session 3 PR does not run Session 2 CI.
- The Agentic_DevOps/ directory must remain untouched by any change in
  this proposal.

## License
- Documentation content: CC BY 4.0 (existing convention).
- Code (Lambda handlers, Terraform, scripts): Apache 2.0 (existing
  convention). All new code files MUST include a brief Apache 2.0 SPDX
  header.

## Tech stack (MLOps_Deployment_Workshop)
- AWS SageMaker, Lambda (Python 3.12), S3, CloudWatch, EventBridge, API Gateway
- Terraform 1.6+ (HCL)
- GitHub Actions
- Python 3.12 for Lambda code and supporting scripts
- scikit-learn for model training (lab-scale)

## Region
us-east-1 for all MLOps_Deployment_Workshop sessions.

## Cross-session resource lifecycle
- Session 1 produces: `workshop-lab-{attendee-id}-production` SageMaker
  endpoint. Must remain InService through June 4.
- Session 2 promotes a challenger; the new champion must remain InService
  through June 16 (Session 3 dependency).
- Session 3 consumes the post-Session-2 endpoint.

Carry-cost between sessions is acknowledged; FinOps approves the
multi-week endpoint hold separately per session.
