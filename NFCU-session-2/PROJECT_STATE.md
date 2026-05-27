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
- [ ] 8. Session 2 Terraform (5 modules + main composition)
- [x] 9. GitHub Actions workflows (deploy/promote/rollback/ci) — YAML valid
- [x] 10. promotion-criteria.yaml
- [x] 11. Lab guide + docs (LAB_GUIDE, architecture, runbook, why-fanout, README)
- [~] 12. Testing — pytest 19 pass, 95% cov on handlers; terraform validate pending Section 8
- [x] 13. Scripts (validate-session-2, provision, teardown, verify-endpoints, trigger-traffic)
- [ ] 14. Acceptance verification — PARTIAL (agreement rate local; rest DEFERRED)

## Last completed step
Sections 5,6,7,10,12: three Lambdas + shared criteria evaluator + tests (19 pass, 95% cov). Challenger retune (8/150->16/80/mf=0.3) still flagged.

## Next step
Await Terraform agent (Section 8), then run validate-session-2.sh + validate-local.sh end-to-end; Section 14 partial.

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
