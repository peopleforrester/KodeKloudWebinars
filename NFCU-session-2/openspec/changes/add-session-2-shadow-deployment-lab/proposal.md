# Proposal: Add Session 2 Shadow Deployment Lab

## Intent
Build the executable lab artifacts for NFCU MLOps Workshop Session 2
(June 4, 2026) inside the
`MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/` subdirectory of
the existing KodeKloudWebinars repo. 25–30 attendees clone the repo,
work inside the Session 2 directory, and operate the lab during the live
2-hour session. The lab teaches the champion-challenger shadow deployment
pattern while preserving the "zero member impact" design property that
regulated financial services require for any meaningful model evaluation.

This is also the first runnable lab in a repo that has been
documentation-only. The proposal introduces the necessary repo-wide
tooling (pyproject.toml, pre-commit, CI) while ensuring the existing
Agentic_DevOps/ webinar collateral is unaffected.

## Scope

In scope, under `MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/`:
- Two trained scikit-learn models (champion v1.0.0, challenger v1.0.1)
- Three Lambda functions: shadow-mirror, comparison, traffic-generator
- Terraform modules and root composition
- promotion-criteria.yaml
- CloudWatch dashboard
- LAB_GUIDE.md, README.md, docs/
- Tests with ≥80% line coverage on Lambda handlers

In scope at repo root:
- Three GitHub Actions workflows in `.github/workflows/`, prefixed
  `session-2-*`, path-filtered to the session directory
- Repo-wide tooling: pyproject.toml, .pre-commit-config.yaml, Makefile,
  scripts/validate-local.sh — all configured to exclude Agentic_DevOps/
- Extended .gitignore for Python and Terraform
- Updated CLAUDE.md to reflect added stacks
- Updated root README.md to add the new webinar section
- `shared/terraform-modules/audit_trail/` (reused by Session 3)
- `MLOps_Deployment_Workshop/README.md` with session index
- Placeholder READMEs for Sessions 1, 3, 4
- Single root-level openspec/ install

Out of scope:
- Any modification to Agentic_DevOps/
- True production shadow deployment
- Real-time streaming comparison
- SageMaker Shadow Variants native implementation (documented, not used)
- Kubernetes-native shadow via Istio or Seldon (Session 4)
- Custom richer demographic features
- Auto-rollback on production telemetry (Session 3)
- Sessions 1, 3, 4 lab artifacts (separate change proposals)
- Any NFCU-specific or proprietary data
- Production-grade audit controls (MFA-delete, object-lock, multi-actor
  approval) — documented as gaps

## Approach
Lambda fan-out over two SageMaker endpoints, async challenger invocation
to preserve caller latency. Scheduled comparison Lambda reads shadow logs
every 5 minutes, emits custom CloudWatch metrics, writes a comparison
summary tagged with promotion_check_status. The
session-2-promote-challenger workflow reads the latest summary, evaluates
against promotion-criteria.yaml, and either refuses to flip or updates
the shadow-mirror Lambda's environment variables to swap
champion/challenger. Rollback is the reverse. Both emit S3 audit-trail
entries with full context.

## Risks
- SageMaker endpoint quota — verify before May 25
- ~92% agreement-rate engineering — dry-run by May 30 must verify
- Session 1 sandbox preservation through June 4
- Carry cost $1,650–$2,400 for June 4 → June 16; FinOps sign-off required
- Path-filter correctness — a missed filter means Session 2 workflows
  fire on Agentic_DevOps PRs or Session 3 PRs
- Repo identity shift — first runnable lab in a collateral-only repo;
  if the team prefers separation, prefer a separate code repo
