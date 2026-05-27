# Tasks — `monitoring` (NFCU Session 3)

> Split from `NFCU-session-3/OPENSPEC_CHANGE_monitoring.md` §3. Paths are relative
> to the repo root. Checkboxes reflect build status in this environment. Items
> requiring live AWS, Docker image builds, browser rendering, or the ≥ June 9 pin
> re-verification are marked **[deferred: <reason>]** — authored to spec but not
> executable here. See `../../../RUN_CONFIG.md`.

## Phase 1: Repository scaffold (by May 30)

- [x] **1.1** Create `NFCU-session-3/` subtree per §2; peers untouched.
- [x] **1.2** Create `openspec/changes/monitoring/` (proposal/design/tasks + 8 delta specs) + `openspec/project.md`.
- [x] **1.3** `README.md` — session overview, role-based starting points.
- [x] **1.4** `resources.md` — external reading list (3–5 refs).
- [x] **1.5** `pyproject.toml` — Python 3.11, pinned dev deps; `pytest tests/` runs.
- [x] **1.6** `.github/workflows/nfcu-session-3-deploy-monitoring.yml` — actionlint clean. *(nested per build override)*
- [x] **1.7** `scripts/capture-reference-distribution.py` → `reference.parquet` (8 features, ≥1000 rows).

## Phase 2: Drift detector + PSI (by May 31)

- [x] **2.1** `lambdas/drift-detector/psi.py` `compute_psi`; `tests/test_psi.py` (identical≈0, shifted>0.25, zero-bin epsilon).
- [x] **2.2** `lambdas/drift-detector/handler.py`; moto-mocked S3+CloudWatch integration test; D3 workshop-only comment.
- [x] **2.3** EventBridge `rate(2 minutes)` in `infra/per-attendee.tf`; `terraform validate`.

## Phase 3: Drift simulator (by June 1)

- [x] **3.1** `lambdas/drift-simulator/handler.py`; test: drifted feature only, ~3000 reqs.
- [x] **3.2** Lab-2 timing documented in `tests/timing_results.md`. **[deferred: live endpoint timing]**

## Phase 4: Evidently runner (by June 2; pin re-verify ≥ June 9)

- [ ] **4.1** Re-verify `evidently` pin. **[deferred: date-gated ≥ June 9]**
- [x] **4.2** `lambdas/evidently-runner/Dockerfile` (py3.11, 1024 MB). Build size **[deferred: ECR build]**.
- [x] **4.3** `handler.py` 0.7.x API; `tests/test_evidently_handler.py` (mocked S3, no `column_mapping`, signed-URL fmt).
- [ ] **4.4** Browser render of report. **[deferred: browser/live]**

## Phase 5: NannyML runner (by June 2; pin re-verify ≥ June 9)

- [ ] **5.1** Re-verify NannyML pin. **[deferred: date-gated ≥ June 9]**
- [x] **5.2** `lambdas/nannyml-runner/Dockerfile` (py3.11, 1024 MB). Build **[deferred: ECR build]**.
- [x] **5.3** `handler.py` CBPE binary; unit test on AUC-delta contract. Real-data delta **[deferred: live]**.
- [x] **5.4** Lab-3 timing documented in `tests/timing_results.md`. **[deferred: live]**

## Phase 6: Incident simulator (by June 3)

- [x] **6.1** Five scenario modules with `trigger()`/`cleanup()`; scenario 3 uses variant-swap alt (OQ4).
- [x] **6.2** Round-robin handler; `tests/test_incident_simulator_round_robin.py` (6 each across 30).
- [x] **6.3** Per-scenario cleanup/alarm verification in `tests/scenario_dry_run.md`. **[deferred: live alarms]**

## Phase 7: Dashboard, alarms, infra (by June 4)

- [x] **7.1** `monitoring/dashboard.json` (2 rows). Render **[deferred: live]**.
- [x] **7.2** `monitoring/alarms.tf` (3 alarms + SNS); `terraform validate`.
- [x] **7.3** `infra/per-attendee.tf` (+ variables/outputs); least-priv IAM; `terraform validate`. Apply **[deferred: live]**.
- [x] **7.4** Provisioning runbook in `LAB_GUIDE.md`.

## Phase 8: Restore script + pre-flight (by June 4)

- [x] **8.1** Baseline `model.tar.gz` (sklearn UCI Adult, SageMaker layout) in `shared/baseline-models/`.
- [x] **8.2** `scripts/restore-session2-endpoint.sh` (idempotent, ≤4 min). Wall-clock **[deferred: live]**.
- [x] **8.3** `scripts/verify-lab-readiness.sh` (30 parallel, green/red).

## Phase 9: Runbooks (by June 5)

- [x] **9.1** `runbooks/runbook-template.md` (5 phases; routing rule top).
- [x] **9.2** Five incident runbooks; D6 note in concept-drift; D12 compliance (grep-clean).

## Phase 10: Validation + readiness (by June 11)

- [x] **10.1** Local suite pristine; terraform validate; actionlint; grep audit. Full dry-run **[deferred: live]**.
- [ ] **10.2** Lab-2 PSI < 5 min. **[deferred: live]**
- [ ] **10.3** NannyML delta > 0.01. **[deferred: live]**
- [ ] **10.4** Five scenarios fire + cleanup. **[deferred: live]**
- [ ] **10.5** Evidently signed URL render. **[deferred: live/browser]**
- [ ] **10.6** 30 sandboxes provisioned. **[deferred: live AWS]**
- [x] **10.7** Lab-assistant briefing doc.
