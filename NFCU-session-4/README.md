# NFCU Session 4 — Kubernetes-Native ML Serving with KServe

Collateral for Session 4 of the NFCU "ML Model Deployment for DevOps" webinar series.
**Live workshop: June 18, 2026.** Four hands-on labs in 120 minutes, on a CPU-only
Kubernetes cluster running KServe in Knative deployment mode.

Sessions 1–3 deploy the same workload on SageMaker. Session 4 moves it to
Kubernetes-native serving: an `InferenceService` you can scale to zero, a small LLM
on CPU, per-model cost attribution, and a canary rollout with rollback.

This directory is meant to be re-run the week after you watch the session — not filed
away. Everything here runs on a local `kind` cluster with no AWS spend, or on your own
EKS cluster via the included Terraform.

## Start here, by role

### Platform Engineer

You want to understand KServe's serving model and run it yourself.

1. Read `reference-card/kserve-on-k8s.md` — the one-page mental model.
2. Bring up a local cluster: `cluster/local/up.sh` (16 GB RAM laptop, ~15 min).
3. Work the four walkthroughs in `attendee-guide/` in order.

### DevOps Engineer

You care about autoscaling behavior, cost, and safe rollouts.

1. Lab 2 (`attendee-guide/lab-2-load-test-and-scaling.md`) contrasts KServe
   concurrency-based scaling against a plain CPU HPA — run both `tests/load/` scripts
   and compare with `tests/load/compare-scaling.sh`.
2. Lab 3 covers per-model cost attribution with OpenCost.
3. Lab 4 is canary → promote → rollback with `canaryTrafficPercent`.

### Lab Engineer (KodeKloud lab platform)

You provision the per-attendee environments and sign off the Definition-of-Done.

1. `runbook/definition-of-done.md` — five dated gates; the last hard gate is the
   June 13 dry run.
2. `cluster/lab-overlays/` — the kustomize base + sample overlay you stamp per attendee.
3. `runbook/troubleshooting-matrix.md` and `runbook/day-of-operations.md` for session day.

### Speaker

You run the live demo and rehearse beforehand.

1. Rehearse on `kind` with no AWS spend: `rehearsal/run-full-session-local.sh`.
2. For the live cluster: `cluster/eks/` (Terraform) + `runbook/speaker-aws-spend.md`
   for the cost you'll see on the bill.
3. `runbook/day-of-operations.md` — T-60 min through T+30 min.

## What's in this directory

| Path | Contents |
|---|---|
| `attendee-guide/` | Prerequisites, four lab walkthroughs, FAQ, post-session actions, and the AWS self-service reproduction guide |
| `reference-card/` | One-page print-friendly KServe reference |
| `manifests/` | The four lab manifests, the HPA baseline, the GPU reference (`.disabled`), and the deterministic model-artifact generator |
| `predictors/tinyllama/` | The custom KServe predictor image for TinyLlama 1.1B (CPU), with a distilGPT-2 fallback |
| `tests/` | Smoke curl tests and k6 load scripts for each lab's traffic pattern |
| `cluster/eks/` | Terraform for a speaker-owned EKS demo cluster |
| `cluster/addons/` | Shared add-ons bootstrap (cert-manager, Knative, Kourier, KServe, Prometheus/Grafana, OpenCost) for both EKS and kind |
| `cluster/local/` | kind cluster for laptop rehearsal |
| `cluster/lab-overlays/` | kustomize base + sample overlay for per-attendee namespaces |
| `rehearsal/` | End-to-end scripts (local and EKS) plus timing notes |
| `runbook/` | Definition-of-Done, troubleshooting matrix, day-of timeline, cleanup, dry-run checklist, AWS spend |
| `openspec/` | The OpenSpec change proposal and capability specs that drove this build |
| `Makefile` | `validate`, `bootstrap-local`, `teardown-local`, `eks-up`, `eks-down`, `build-predictor`, `run-rehearsal`, `clean` |

## Stack

Kubernetes 1.34+ · KServe 0.16+ (Knative mode) · Knative Serving + Kourier ·
OpenCost · Prometheus + Grafana · Python 3.12+ predictor · k6 0.57+ · Terraform 1.10+
(EKS). CPU-only — GPU patterns ship as commented reference only.

## A note on scope

This collateral is self-contained under `NFCU-session-4/`. It does not provision the
KodeKloud lab platform's per-attendee EKS workflow (the platform owns that; we ship the
overlays it consumes). See `openspec/changes/add-nfcu-session-4-kserve-collateral/` for
the full proposal and `RUN_CONFIG.md` for build-time decisions.
