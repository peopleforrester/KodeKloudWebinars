# PROJECT_STATE — NFCU-session-4 (add-nfcu-session-4-kserve-collateral)

## Goal

Implement the Session 4 KServe ML-serving collateral per
`OPENSPEC_CHANGE_session-4-kserve-serving.md`, **entirely under `NFCU-session-4/`**.
Do not touch the repo root (see `RUN_CONFIG.md` for the path mapping and deviations).

## Working location (IMPORTANT)

All work is in an **isolated git worktree**: `/home/michael/repos/_archive/kk/kk-nfcu-session-4/`.
The original clone `/home/michael/repos/_archive/kk/KodeKloudWebinars/` is shared by other
concurrent sessions (sessions 1/2/3) and kept switching branches under us, so Session 4
moved to its own worktree on 2026-05-27. Do NOT resume work in the shared clone.
Recovery tags (in the shared repo's object store): `nfcu-s4-phase0-scaffold`, `nfcu-s4-phase2-eks`.

## Branch & verification

- Branch: `nfcu-session-4-build` in the worktree above, cut from clean `main` (59a6ec7).
  Session-4 commits only — no session-1/2/3 dirs. No commits to `main`. No push without go-ahead.
- Verification method: **static / authoring only** in this environment. Tools present:
  terraform 1.15.4, kubectl v1.36.1, helm, kind 0.24.0, docker, python3, yamllint,
  markdownlint, jq. Missing: kustomize (`kubectl kustomize` used instead), hadolint, k6.
- **Verified:** file structure, `terraform validate`/`fmt`, `yamllint`, `markdownlint`,
  `kubectl kustomize build`, `bash -n`, `python -m py_compile` — whatever the phase produces.
- **NOT verified (needs real cluster/AWS/Docker the speaker runs):** `terraform apply`,
  live kind bootstrap, end-to-end rehearsal, multi-arch image build/push, k6 execution,
  `kubectl --dry-run=client` against KServe CRDs (CRDs absent locally).

## Phase checklist

- [x] Phase 0 — Ingest: spec saved verbatim, RUN_CONFIG, nested openspec scaffolding (project.md, proposal/tasks/design, 9 spec deltas), PROJECT_STATE
- [x] Phase 1 — Repo scaffolding: README, .gitignore, Makefile, validate harness (root README edit deferred)
- [x] Phase 2 — EKS Terraform module (cluster/eks) — terraform validate passes against real modules
- [x] Phase 3 — Cluster add-ons bootstrap (cluster/addons) — bootstrap.sh, verify.sh, 7 version-pinned helm-values
- [x] Phase 4 — Local kind cluster (cluster/local)
- [x] Phase 5 — Lab overlays (cluster/lab-overlays)
- [ ] Phase 6 — InferenceService manifests (manifests/)
- [ ] Phase 7 — TinyLlama predictor image (predictors/tinyllama)
- [ ] Phase 8 — Load test harness (tests/)
- [ ] Phase 9 — Attendee collateral (attendee-guide, reference-card)
- [ ] Phase 10 — Operations runbook (runbook/)
- [ ] Phase 11 — Rehearsal path (rehearsal/)
- [ ] Phase 12 — CI/Makefile validate, final sweep, archive specs → openspec/specs

## Last completed step

Phase 4 complete. Local kind path: kind-config.yaml (1 cp + 2 workers, ports 80/443/31080),
idempotent up.sh (create + bootstrap local + verify), down.sh, README with 16 GB min spec.

## Next step

Phase 5 — `cluster/lab-overlays/`: kustomize base (namespace, resourcequota 4cpu/8Gi/10pods,
deny-cross-namespace networkpolicy, serviceaccount with IRSA annotation placeholder) +
attendee-sample overlay + README. Validate with `kubectl kustomize build`.

## Notes / decisions

- Task 1.3 (root README link) and 12.1 (root `.github/`) are deferred/rebased per scope.
- Live-cluster acceptance items are authored + statically validated only.
- The `validate` Makefile target is the local test harness (k6/hadolint absent, skipped gracefully).
