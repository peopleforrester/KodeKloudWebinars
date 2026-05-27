# Lab Manifests

The Kubernetes manifests for the four labs, indexed by lab. Apply them into an attendee
namespace (see `cluster/lab-overlays/`). Before applying the XGBoost ones, set `storageUri`
to match your cluster (S3 on EKS, PVC locally) — each file's header explains how.

| File | Lab | What it does |
|---|---|---|
| `lab1-xgboost-inferenceservice.yaml` | 1 | XGBoost v1.0.0 as a KServe InferenceService. `minReplicas: 0`, `maxReplicas: 5`, `containerConcurrency: 50`. Scale-to-zero + concurrency autoscaling. |
| `lab2-hpa-baseline-deployment.yaml` | 2 | The same model as a plain Deployment + Service + CPU HPA (50%, 1→5). The "wrong way" baseline to contrast with Lab 1. |
| `lab3-tinyllama-inferenceservice.yaml` | 3 | TinyLlama 1.1B via the custom CPU predictor. `containerConcurrency: 5`, 4–6 Gi memory, no GPU. |
| `lab4-xgboost-canary-v1-0-1.yaml` | 4 | Canary: bumps the Lab 1 service to v1.0.1 at `canaryTrafficPercent: 10`. |
| `lab4-xgboost-promote.yaml` | 4 | Promote: `canaryTrafficPercent` removed → 100% v1.0.1. |
| `lab4-xgboost-rollback.yaml` | 4 | Rollback: `canaryTrafficPercent: 0` → 100% back to v1.0.0. |
| `_reference-gpu-vllm.yaml.disabled` | — | GPU + vLLM reference. The `.disabled` suffix keeps it out of `kubectl apply -f manifests/`. Never applies on the CPU lab cluster. |
| `model-artifacts/` | — | Deterministic generator for the v1.0.0 / v1.0.1 `.bst` files, plus the S3 upload script. |

## Bulk apply note

`kubectl apply -f manifests/` reads only `*.yaml` / `*.yml` / `*.json`, so the
`_reference-gpu-vllm.yaml.disabled` file is skipped — no GPU resources are ever requested.
The Lab 4 files share the Lab 1 InferenceService name (`adult-income-classifier`) on
purpose: each is applied in sequence to the *same* service to drive the canary → promote →
rollback flow.

## Validation

`kubectl apply --dry-run=client` works for the Lab 2 built-in types offline. The
InferenceService manifests need the KServe CRDs registered, so validate those against a
cluster that has run `cluster/addons/bootstrap.sh` (or `--dry-run=server`).
