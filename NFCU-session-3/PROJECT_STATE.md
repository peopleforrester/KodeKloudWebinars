# PROJECT_STATE — NFCU Session 3 (`monitoring`)

**Goal:** Build the NFCU-session-3 lab environment to completion per
`OPENSPEC_CHANGE_monitoring.md`. Everything nested under `NFCU-session-3/`.

**Status:** Build complete in this environment (all locally-verifiable acceptance
criteria pass). Live-AWS / Docker-build / browser / ≥ June 9 pin items are
authored-to-spec and explicitly deferred (tracked, not falsely passed).

## Branch reality (IMPORTANT — read before integrating)

This working tree is shared by parallel agents building NFCU sessions 1, 2, 3, 4.
HEAD moved between branches during the work, so all commits (mine + the other
sessions') landed interleaved on a single branch line whose current tip is my
Phase 9/10 work. My NFCU-session-3 commits are intact and **every one was scoped
to `NFCU-session-3/` only** (verified per commit). The branch I created,
`feat/nfcu-session-3-monitoring`, never advanced past the base — the real commits
are on the currently-checked-out branch. Michael should reconcile branches to his
workflow before any push; do NOT untangle destructively without his go-ahead.

## Verification method

Local TDD (pytest 22 passing + moto), `terraform validate`/`fmt`, `actionlint`,
`shellcheck`, JSON validation, D12 grep audit, reproducible artifact builds.
Live AWS, Docker image builds, browser rendering, and the date-gated pin
re-verification are out-of-environment — see `RUN_CONFIG.md` and
`tests/dry_run_results.md`.

## Phase checklist — ALL COMPLETE (local)

- [x] **Phase 1** — Scaffold + OpenSpec artifacts + capture script (reference.parquet 15,315×8)
- [x] **Phase 2** — Drift detector + PSI (7 PSI tests, moto integration), EventBridge rate(2 min)
- [x] **Phase 3** — Drift simulator (3000 reqs, hours_per_week only)
- [x] **Phase 4** — Evidently runner (verified 0.7.x API; pin re-verify deferred ≥ Jun 9)
- [x] **Phase 5** — NannyML CBPE runner (verified API; pin re-verify deferred ≥ Jun 9)
- [x] **Phase 6** — Incident simulator (round-robin 6×5/30, five scenarios, OQ4 variant-swap)
- [x] **Phase 7** — Dashboard (2 rows) + three alarms + SNS (terraform valid)
- [x] **Phase 8** — Baseline model.tar.gz (~0.83 acc) + restore + readiness scripts
- [x] **Phase 9** — Runbook template + five runbooks (D6 note, D12 clean)
- [x] **Phase 10** — Full local verification sweep, dry-run docs, assistant briefing, state

## Remaining (out of this environment)

- Live dry-run on a real sandbox (10.1–10.6) — June 11.
- Evidently/NannyML pin re-verification (4.1/5.1) — ≥ June 9.
- Container image builds against ECR (4.2/5.2).
- Branch reconciliation to Michael's workflow before any push.

## Open questions carried from spec §6 (for Michael)

- OQ3: shared S3 bucket name/region for the baseline artifact (suggested
  `kodekloud-mlops-shared-artifacts-us-east-1`, prefix `nfcu-session-3/baseline-model/`).
- OQ4: prediction-drift-isolated implemented via SageMaker endpoint-config swap
  (in-scope alternative); confirm inverted/baseline configs exist in the sandbox.
- OQ7: repo-root `CLAUDE.md` stack line was updated (by another process) to note
  the runnable code — done, outside this change's boundary.
