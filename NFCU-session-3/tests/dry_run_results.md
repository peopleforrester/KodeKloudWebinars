# Dry-Run Results

**Verification method:** Two tiers.

1. **Local (done now, in the build environment):** unit + moto-mocked integration
   tests, `terraform validate`/`fmt`, `actionlint`, `shellcheck`, JSON validation,
   and the D12 token audit. All green.
2. **Live (deferred to the June 11 dry-run):** anything requiring a real AWS
   sandbox, Docker image builds against ECR, a browser, or the ≥ June 9 pin
   re-verification. These are listed below as **deferred** — not marked passed.
   See `../RUN_CONFIG.md`.

## Local verification (build environment) — PASS

| Check | Command | Result |
|-------|---------|--------|
| Unit + integration tests | `pytest tests/` | **22 passed** |
| PSI math | `test_psi.py` | identical≈0, shifted>0.25, zero-bin finite, categorical |
| drift-detector | `test_drift_detector.py` | per-feature metrics + alarm transition (moto) |
| drift-simulator | `test_drift_simulator.py` | 3000 reqs, only hours_per_week shifted |
| evidently-runner | `test_evidently_handler.py` | 0.7.x API, no column-mapping, signed URL |
| nannyml-runner | `test_nannyml_handler.py` | CBPE wiring, AUC delta, metric emit |
| incident-simulator | `test_incident_simulator_round_robin.py` | 6 each / 30, dispatch, trigger/cleanup |
| Terraform (infra) | `terraform validate` | **valid: true**, fmt clean |
| Terraform (monitoring) | `terraform validate` | **valid: true**, fmt clean |
| Workflow | `actionlint` | clean |
| Shell scripts | `shellcheck` | clean |
| Dashboard | `json.load(dashboard.json)` | valid, 7 widgets |
| D12 audit | grep NCUA/FFIEC/compliance/bank | runbooks clean; only the prohibition note in LAB_GUIDE |
| Reference capture | `capture-reference-distribution.py` | 15,315 rows × 8 features |
| Baseline model | `build-baseline-model.py` | SageMaker-compatible tar.gz, ~0.83 acc |
| Readiness logic | stub-`aws` run | distinguishes healthy (GREEN) / broken (RED) |

## Live dry-run (deferred to June 11) — PENDING

| Task | Acceptance | Status |
|------|-----------|--------|
| 10.1 | End-to-end run in workshop timing | deferred (live sandbox) |
| 10.2 | Lab 2 PSI crosses 0.25 within 5 min | deferred — see `timing_results.md` |
| 10.3 | NannyML AUC delta > 0.01 on drifted window | deferred (real CBPE on fixtures) |
| 10.4 | Five scenarios fire alarms + auto-cleanup | deferred — see `scenario_dry_run.md` |
| 10.5 | Evidently signed URL renders for 1h | deferred (browser) |
| 10.6 | 30 sandboxes provisioned (terraform apply) | deferred (live AWS) |
| 4.1 / 5.1 | Evidently / NannyML pin re-verify | deferred — date-gated ≥ June 9 |
| 4.2 / 5.2 | Container images build < 1.5 GB | deferred (ECR build) |

## Pre-session sequence (run on a real sandbox)

1. `scripts/build-baseline-model.py` → upload `model.tar.gz` to the shared bucket.
2. `scripts/capture-reference-distribution.py` → upload `reference.parquet` per attendee.
3. Provision via the workflow or `terraform apply` (infra + monitoring) per attendee.
4. `scripts/verify-lab-readiness.sh --cohort cohort.txt` until all green.
5. Walk Labs 1–4 as one attendee; fill in `timing_results.md` and `scenario_dry_run.md`.
