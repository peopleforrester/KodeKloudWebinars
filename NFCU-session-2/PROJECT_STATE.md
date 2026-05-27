# PROJECT_STATE — NFCU Session 2 Shadow Deployment Lab

## Plan summary
Execute the OpenSpec change `add-session-2-shadow-deployment-lab` (latest spec)
to completion. Everything is contained under `NFCU-session-2/`, which acts as
the spec's "repo root" (per Michael's instruction: keep everything under
NFCU-session-2, ignore sibling folders). The spec's internal directory names
are preserved verbatim (`MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/`,
`shared/`, `.github/`, `openspec/`) — no renaming.

## Verification method
- OpenSpec: `openspec validate --strict` (PASSING).
- Python: ruff + mypy --strict + pytest (Python 3.12 venv at `.venv/`).
- Terraform: terraform fmt/validate + tflint + tfsec + checkov + kics.
- Models: `verify_agreement.py` must report 90–94% agreement (real sklearn run).
- NOT verified here (requires live env / human): terraform apply to AWS,
  SageMaker endpoints, live GitHub Actions PR-trigger tests, FinOps sign-off,
  May 30 lab-engineer dry-run. These are DEFERRED, documented below.

## Environment
- Branch: `add-session-2-shadow-deployment-lab` (off `feat/nfcu-session-3-monitoring`).
- Python venv: `NFCU-session-2/.venv` (CPython 3.12.13) via uv.
- Installed: ruff 0.15, mypy 2.1, pytest 9, sklearn 1.8, pandas, numpy, moto,
  boto3, pyyaml, checkov 3.2, pre-commit 4.6. System: terraform, tflint,
  tfsec 1.28, kics 2.1, gh, aws.
- NOT pushing without explicit permission.

## Task checklist (sections from tasks.md; 95 leaf tasks)
- [x] 0. Ingest spec into openspec/ canonical files + `openspec validate --strict` PASS
- [x] 1. Repo-wide bootstrap (.gitignore, pyproject, Makefile, pre-commit, validate-local.sh, README, CLAUDE)
- [x] 2. MLOps_Deployment_Workshop scaffolding (README + placeholder sessions)
- [x] 3. Shared audit_trail Terraform module — tfsec/checkov/tflint/fmt GREEN
- [x] 4. Session 2 model training — agreement 0.9284 (in 90-94% band); challenger retuned per spec validation clause
- [x] 5. Lambda: shadow-mirror + tests (98% cov)
- [x] 6. Lambda: comparison + tests (96% cov)
- [x] 7. Lambda: traffic-generator + tests (89% cov)
- [x] 8. Session 2 Terraform (5 modules + composition + SageMaker) — fmt/validate/tflint/tfsec(90 pass,0 prob)/checkov(151 pass,0 fail)/kics(0 high+crit) GREEN
- [x] 9. GitHub Actions workflows (deploy/promote/rollback/ci) — YAML valid; path-filters verified
- [x] 10. promotion-criteria.yaml
- [x] 11. Lab guide + docs (LAB_GUIDE, architecture, runbook, why-fanout, README)
- [x] 12. Testing — pytest 19 pass, 97% total cov; validate-session-2.sh + validate-local.sh exit 0
- [x] 13. Scripts (validate-session-2, provision, teardown, verify-endpoints, trigger-traffic)
- [~] 14. Acceptance verification — locally verifiable items DONE; live-AWS items DEFERRED (below)

## Definition of Done status
- [x] validate-local.sh exits 0 from repo root (97% cov, 19 tests)
- [x] validate-session-2.sh exits 0 standalone
- [x] All Terraform modules pass terraform validate
- [x] Checkov/tfsec/tflint zero unaddressed findings (kics 0 high/crit)
- [x] pytest 0 failures, >=80% on handlers (96/96/89/100%)
- [x] verify_agreement.py reports 0.9284 (in 90-94%)
- [x] Promotion gate evaluates BOTH pass and fail (criteria.py unit + CLI tests)
- [x] Audit entry schema has all 8 required fields (static check)
- [x] LAB_GUIDE caveats present; README prod-vs-lab gaps present
- [x] Path-filters: no session-2 workflow references Agentic_DevOps/Session_3
- [ ] DEFERRED (need live env/human): terraform apply to AWS, SageMaker endpoints,
      live Actions PR-trigger runs (14.7/14.8 logic verified statically),
      lab-engineer dry-run (14.1), per-attendee cost (14.6), FinOps sign-off

## Last completed step
End-to-end: validate-session-2.sh and validate-local.sh both exit 0. All 14
sections complete to the extent achievable without live AWS.

## Next step
None outstanding for the local build. Remaining items require a live AWS sandbox
and human sign-off (see DEFERRED above). Awaiting Michael's call on the two flags
(challenger hyperparameters; workflow placement under NFCU-session-2/.github/).

## Containment / deviation notes
- `Agentic_DevOps/` does not exist under NFCU-session-2; isolation tasks are
  trivially satisfied. Tooling configs keep the `Agentic_DevOps` exclusions
  verbatim (harmless here) per "don't deviate."
- Two delta-spec requirement lines were reflowed so the RFC-2119 keyword lands
  on the requirement's first line (OpenSpec strict parser requirement). Intent
  unchanged. Authorized by spec hand-off step 6 ("address structural findings").

## Deferred (cannot complete in this environment)
- 14.1 lab-engineer dry-run (May 30); 14.3/14.4 live workflow runs; 14.6 cost;
  14.7/14.8 live Actions path-filter trigger tests (logic is unit-tested instead).
- FinOps carry-cost sign-off.
- Actual `terraform apply`, SageMaker endpoint provisioning.
