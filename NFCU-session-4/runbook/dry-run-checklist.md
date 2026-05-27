# Dry-Run Checklist (complete by 2026-06-13)

A full end-to-end rehearsal against the provisioned cluster, five days before the session.
Execute every step; log any failure and triage it against
[`troubleshooting-matrix.md`](troubleshooting-matrix.md). **All blocking issues must be
resolved before 2026-06-18.** This is DoD Gate 3.

## Setup

- [ ] Run on the actual shared cluster (or a faithful copy), not just local kind.
- [ ] `cluster/addons/verify.sh` exits 0.
- [ ] A sample attendee namespace is stamped and reachable.

## Labs, each within its time budget

- [ ] **Lab 1** (≤12 min): deploy `adult-income-classifier`, get a 200 prediction, observe
      scale-to-zero after ~60s and cold-start back. Record the cold-start time.
- [ ] **Lab 2** (≤12 min): deploy HPA baseline, run both k6 ramps, `compare-scaling.sh`
      prints a row per approach with KServe scaling up earlier.
- [ ] **Lab 3** (≤15 min): deploy TinyLlama, get a non-empty completion, k6 LLM run keeps
      errors <1%, OpenCost shows a distinct per-model cost. Record LLM cold-start time.
- [ ] **Lab 4** (≤15 min): canary to 10% (verify 8–12% split), promote to 100%, roll back to
      v1.0.0 with no pod restart.

## Resilience checks

- [ ] Kill a predictor pod mid-lab; confirm it recovers.
- [ ] Force the distilGPT-2 fallback path for Lab 3; confirm the same API/response contract.
- [ ] Exceed the ResourceQuota deliberately; confirm the API rejects with a clear quota error.
- [ ] Confirm cross-namespace traffic is blocked but Knative ingress still routes.

## Observability

- [ ] Grafana: Knative/KServe dashboards show request rate and pod counts during a k6 run.
- [ ] OpenCost: per-model cost populates within the run.
- [ ] `kubectl get revisions` reflects the canary split.

## Sign-off

- [ ] Cold-start times recorded in `rehearsal/timing-notes.md`.
- [ ] Every failure logged with its matrix row and resolution.
- [ ] No open blockers. Initial and date here: ____________________
