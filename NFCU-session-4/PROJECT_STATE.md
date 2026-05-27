# PROJECT_STATE — NFCU-session-4 (add-nfcu-session-4-kserve-collateral)

## Goal

Implement the Session 4 KServe ML-serving collateral per
`OPENSPEC_CHANGE_session-4-kserve-serving.md`, **entirely under `NFCU-session-4/`**.
Do not touch the repo root (see `RUN_CONFIG.md` for the path mapping and deviations).

## Branch & verification

- Branch: `nfcu-session-4-build` (cut from `main`). No commits to `main`. No push without go-ahead.
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
- [ ] Phase 1 — Repo scaffolding: README, .gitignore, Makefile (root README edit deferred)
- [x] Phase 2 — EKS Terraform module (cluster/eks) — terraform validate passes against real modules
- [ ] Phase 3 — Cluster add-ons bootstrap (cluster/addons)
- [ ] Phase 4 — Local kind cluster (cluster/local)
- [ ] Phase 5 — Lab overlays (cluster/lab-overlays)
- [ ] Phase 6 — InferenceService manifests (manifests/)
- [ ] Phase 7 — TinyLlama predictor image (predictors/tinyllama)
- [ ] Phase 8 — Load test harness (tests/)
- [ ] Phase 9 — Attendee collateral (attendee-guide, reference-card)
- [ ] Phase 10 — Operations runbook (runbook/)
- [ ] Phase 11 — Rehearsal path (rehearsal/)
- [ ] Phase 12 — CI/Makefile validate, final sweep, archive specs → openspec/specs

## Last completed step

Phase 2 complete. EKS Terraform module written and `terraform validate`'d against the
real terraform-aws-modules (EKS v20, IAM v5, VPC v5). Cross-platform provider lock committed.

## Next step

Phase 3 — `cluster/addons/`: bootstrap.sh (ordered, idempotent), verify.sh, and
version-pinned helm-values/*.yaml for cert-manager, Knative, Kourier, KServe,
kube-prometheus-stack, OpenCost, and (EKS-only) the AWS Load Balancer Controller.

## Notes / decisions

- Task 1.3 (root README link) and 12.1 (root `.github/`) are deferred/rebased per scope.
- Live-cluster acceptance items are authored + statically validated only.
- The `validate` Makefile target is the local test harness (k6/hadolint absent, skipped gracefully).
