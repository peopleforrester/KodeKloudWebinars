# PROJECT_STATE — NFCU Session 3 (`monitoring`)

**Goal:** Build the NFCU-session-3 lab environment to completion per
`OPENSPEC_CHANGE_monitoring.md`. Everything nested under `NFCU-session-3/`.

**Branch:** `feat/nfcu-session-3-monitoring` (not pushed; no main commits)
**Verification method:** Local TDD (pytest+moto), `terraform validate`,
`actionlint`, grep audits. Live AWS / Docker builds / browser / June-9 pin checks
are out-of-environment and tracked as deferred (see `RUN_CONFIG.md`).

## Plan summary

10 phases from the spec §3. Each phase: write tests/artifacts, run what's locally
runnable, commit. Date-gated and live-AWS acceptance criteria documented as
deferred rather than falsely marked passed.

## Phase checklist

- [ ] **Phase 1** — Scaffold + OpenSpec artifacts + capture script
- [ ] **Phase 2** — Drift detector + PSI math
- [ ] **Phase 3** — Drift simulator
- [ ] **Phase 4** — Evidently runner (pin re-verify deferred to ≥ Jun 9)
- [ ] **Phase 5** — NannyML runner (pin re-verify deferred to ≥ Jun 9)
- [ ] **Phase 6** — Incident simulator (OQ4 scenario-3 alt impl)
- [ ] **Phase 7** — Dashboard + alarms + per-attendee infra
- [ ] **Phase 8** — Restore script + pre-flight readiness
- [ ] **Phase 9** — Runbooks (D12 compliance)
- [ ] **Phase 10** — Validation + dry-run docs + final state

## Last completed step

Setup: branch created, venv + deps installed, spec ingested, RUN_CONFIG written,
tasks #1–#10 created.

## Next step

Phase 1 — scaffold the directory tree and split the spec into OpenSpec artifacts.

## Open questions carried from spec §6 (for Michael, not blocking the build)

- OQ3: shared S3 bucket name/region for baseline artifact (suggested
  `kodekloud-mlops-shared-artifacts-us-east-1`, prefix `nfcu-session-3/baseline-model/`).
- OQ4: prediction-drift-isolated needs an inference-container env-var hook in
  S1/2; if absent, in-scope alternative is a SageMaker model-variant swap inside
  NFCU-session-3 (chosen for the build; documented in the scenario module).
- OQ6/7/8: slide deck location, repo-root CLAUDE.md stack update, OpenSpec-per-
  session precedent — all governed by separate changes, not this build.
