# NFCU Session 4 — Kubernetes-Native ML Serving with KServe

Collateral for Session 4 of the NFCU "ML Model Deployment for DevOps" webinar series.
**Live workshop: June 18, 2026.** Four hands-on labs in 120 minutes, on a CPU-only
Kubernetes cluster running KServe in Knative deployment mode.

Sessions 1–3 deploy the same workload on SageMaker. Session 4 moves it to Kubernetes-native
serving: an `InferenceService` you can scale to zero, a small LLM on CPU, per-model cost
attribution, and a canary rollout with rollback.

This directory is meant to be re-run the week after you watch the session — not filed away.
Everything here runs on a local `kind` cluster with **no AWS spend**, or on your own EKS
cluster via the included Terraform.

## Quickstart

**Local (kind) — no cloud, no spend.** Needs a 16 GB / 4-core laptop with `docker`, `kind`,
`kubectl`, `helm`, `k6`, `python3`.

```bash
bash cluster/local/up.sh            # create kind + install all add-ons (~10-15 min)
bash cluster/addons/verify.sh       # confirm everything is Ready
# then work attendee-guide/lab-1 … lab-4, or run the whole thing:
bash rehearsal/run-full-session-local.sh
```

**EKS — your own AWS account.** Needs AWS CLI v2 (authenticated), Terraform ≥ 1.10,
`kubectl`, `helm`, `docker`. Budget **$40–$70** for an 8-hour window; **always tear down**.

```bash
cd cluster/eks
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
bash up.sh                          # terraform apply (~15-25 min)
bash ../addons/bootstrap.sh eks
# ... work the labs ...
bash down.sh                        # type the cluster name to confirm — stops the meter
```

Full step-by-step: [`attendee-guide/reproduce-on-your-aws-account.md`](attendee-guide/reproduce-on-your-aws-account.md).

## The four labs

| Lab | Time | Teaches | Walkthrough |
|---|---|---|---|
| 1 | 12 min | Deploy an XGBoost `InferenceService`; scale-to-zero | [`lab-1`](attendee-guide/lab-1-deploy-inferenceservice.md) |
| 2 | 12 min | Concurrency autoscaling vs a CPU-HPA baseline | [`lab-2`](attendee-guide/lab-2-load-test-and-scaling.md) |
| 3 | 15 min | A small LLM (TinyLlama, CPU) + per-model cost (OpenCost) | [`lab-3`](attendee-guide/lab-3-llm-and-costs.md) |
| 4 | 15 min | Canary → promote → rollback via `canaryTrafficPercent` | [`lab-4`](attendee-guide/lab-4-canary-rollout.md) |

Start at [`attendee-guide/`](attendee-guide/README.md); prerequisites in
[`attendee-guide/prerequisites.md`](attendee-guide/prerequisites.md).

## Start here, by role

- **Platform Engineer** — read `reference-card/kserve-on-k8s.md` (one-page mental model),
  bring up `cluster/local/`, then work the four walkthroughs.
- **DevOps Engineer** — Lab 2 (autoscaling vs HPA, `tests/load/compare-scaling.sh`), Lab 3
  (cost), Lab 4 (safe rollouts).
- **Lab Engineer** — `runbook/definition-of-done.md` (five dated gates), `cluster/lab-overlays/`
  (per-attendee namespaces), `runbook/troubleshooting-matrix.md` + `runbook/day-of-operations.md`.
- **Speaker** — rehearse with `rehearsal/run-full-session-local.sh`; live demo via
  `cluster/eks/` + `runbook/speaker-aws-spend.md`; `runbook/day-of-operations.md` (T-60 → T+30).

## What's in this directory

| Path | Contents |
|---|---|
| `attendee-guide/` | Prerequisites, four lab walkthroughs, FAQ, post-session actions, AWS reproduction guide |
| `reference-card/` | One-page print-friendly KServe reference |
| `manifests/` | Four lab manifests, the HPA baseline, GPU reference (`.disabled`), deterministic model generator |
| `predictors/tinyllama/` | Custom KServe predictor image for TinyLlama 1.1B (CPU), with a distilGPT-2 fallback |
| `tests/` | Smoke curl tests and k6 load scripts for each lab's traffic pattern |
| `cluster/eks/` | Terraform for a speaker-owned EKS demo cluster |
| `cluster/addons/` | Shared add-ons bootstrap (cert-manager, Knative, Kourier, KServe, Prometheus/Grafana, OpenCost) — same script for EKS and kind |
| `cluster/local/` | kind cluster for laptop rehearsal |
| `cluster/lab-overlays/` | kustomize base + sample overlay for per-attendee namespaces |
| `rehearsal/` | End-to-end scripts (local and EKS) plus timing notes |
| `runbook/` | Definition-of-Done, troubleshooting matrix, day-of timeline, cleanup, dry-run checklist, AWS spend |
| `ci/` | Copy-ready GitHub Actions workflow template + CI notes |
| `scripts/` | The `validate` harness (`validate.sh`, `check-manifests.py`) |
| `openspec/` | The OpenSpec change proposal and capability specs that drove this build |
| `Makefile` | `validate`, `bootstrap-local`, `teardown-local`, `eks-up`, `eks-down`, `build-predictor`, `run-rehearsal`, `clean` |

## Stack and pinned versions

Kubernetes 1.34–1.36 · CPU-only (GPU patterns ship as commented reference). Versions are
pinned in `cluster/addons/bootstrap.sh` and each `helm-values/*.yaml` header:

| Component | Version | | Component | Version |
|---|---|---|---|---|
| KServe | `v0.16.0` | | cert-manager | `v1.16.1` |
| Knative Serving | `1.15.2` | | kube-prometheus-stack | chart `85.3.3` |
| Kourier | `knative-v1.15.0` | | OpenCost | chart `2.5.21` |
| EKS module | `~> 20.0` | | AWS LB Controller | chart `3.3.0` |

The KServe-coupled versions come from KServe 0.16.0's own `quick_install.sh`. The predictor
pins `kserve 0.16`, `transformers 4.50`, `torch 2.5` (CPU), `fastapi 0.115` (Python 3.12+).

## Validate

```bash
make validate     # runs the full static check suite locally and in CI
```

Checks: `yamllint`, `markdownlint`, `terraform fmt`+`validate`, `kubectl kustomize build`,
manifest structure (offline substitute for `kubectl dry-run`), `bash -n`, `py_compile`,
`node --check`. Missing tools are skipped, not failed, so it runs anywhere.

## Key design decisions

- **Knative deployment mode, not Standard** — the session's scale-to-zero, concurrency
  autoscaling, and `canaryTrafficPercent` all require it.
- **Kourier, not Istio/Gateway API** — simplest Knative network layer; no service mesh.
- **EKS module v20 + IRSA, not v21 + Pod Identity** — the design is IRSA-based (storage
  initializer, ALB controller, autoscaler) and v21 removed native IRSA. Pod Identity is the
  more modern choice and is tracked as a possible follow-up; see `cluster/eks/README.md`.
- **TinyLlama on CPU via a custom predictor** — KServe's HF runtime defaults to GPU vLLM;
  a custom CPU predictor keeps the image small and the schema matching the curl examples.
- **Model artifacts generated, not committed** — `generate-xgboost-models.py` is seeded and
  reproducible; `.bst` files stay out of git.

## Status

All build artifacts are authored and **statically validated** (`make validate` passes).
What still needs a live cluster — `terraform apply`, kind bootstrap end-to-end, the
rehearsal, `kubectl` dry-run against the KServe CRDs, the image build/push, and recording
cold-start times — is the **June 13 dry run** (`runbook/dry-run-checklist.md`, DoD Gate 3).
The OpenSpec change is intentionally **not yet archived**, pending that dry run.

## A note on scope

Self-contained under `NFCU-session-4/`. It does not provision the KodeKloud lab platform's
per-attendee EKS workflow (the platform owns that; we ship the overlays it consumes). See
`openspec/changes/add-nfcu-session-4-kserve-collateral/` for the full proposal and
`RUN_CONFIG.md` for build-time decisions and deviations.
