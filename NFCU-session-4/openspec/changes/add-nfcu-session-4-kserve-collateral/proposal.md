# Change: add-nfcu-session-4-kserve-collateral

## Why

Session 4 of the NFCU ML Model Deployment for DevOps webinar series ships June 18, 2026. The session takes 25–30 platform engineers through a Kubernetes-native ML serving workflow on KServe: deploy an InferenceService, exercise concurrency-based autoscaling, deploy a small LLM, observe per-model cost attribution, and execute a canary rollout with rollback. Four hands-on labs in 120 minutes, first lab at the 12-minute mark.

Attendees need durable collateral they can re-run the week after the session — the slides alone are not the deliverable. The lab engineering team needs manifests, container images, k6 scripts, and a runbook before June 6, 2026 (12 business days lead time for Kubernetes provisioning). The speaker needs a personally-owned EKS demo cluster for the live session and a local kind path for rehearsal.

This change adds the `NFCU-session-4/` directory containing all attendee-facing collateral, lab-engineering artifacts, Terraform for a speaker-owned EKS demo cluster, and a locally-runnable rehearsal path on kind.

## What Changes

- **ADDED:** `nfcu-session-4-collateral` capability — attendee-facing docs (README, reference card, four lab walkthroughs, FAQ, post-session resources).
- **ADDED:** `nfcu-session-4-eks-cluster` capability — Terraform module for a speaker-owned EKS cluster (single cluster, 2–3 nodes, m5.xlarge default) suitable for the live demo and post-session attendee reproduction.
- **ADDED:** `nfcu-session-4-cluster-addons` capability — bootstrap automation for KServe 0.16+, Knative Serving, Kourier, OpenCost, Prometheus, Grafana, AWS Load Balancer Controller (EKS only), pinned to specific chart and app versions.
- **ADDED:** `nfcu-session-4-local-cluster` capability — kind-based local cluster bootstrap for speaker rehearsal without AWS spend.
- **ADDED:** `nfcu-session-4-lab-overlays` capability — kustomize overlays for per-attendee namespaces (Namespace + ResourceQuota + NetworkPolicy + ServiceAccount) consumed by the KodeKloud lab platform.
- **ADDED:** `nfcu-session-4-inferenceservice-manifests` capability — four lab manifests (XGBoost v1.0.0, XGBoost v1.0.1 canary, TinyLlama completion endpoint, HPA-baseline Deployment for the Lab 2 comparison) plus model artifact generation script.
- **ADDED:** `nfcu-session-4-tinyllama-predictor-image` capability — custom KServe-compatible container image serving TinyLlama 1.1B on CPU via Hugging Face transformers, with distilGPT-2 fallback. Multi-arch (amd64 + arm64).
- **ADDED:** `nfcu-session-4-load-test-harness` capability — k6 scripts for Lab 2 (concurrency ramp against KServe), Lab 2 baseline (same ramp against HPA Deployment), Lab 3 (LLM load), Lab 4 (steady traffic for canary observation).
- **ADDED:** `nfcu-session-4-operations-runbook` capability — Definition-of-Done checklist, troubleshooting matrix, day-of-session operations guide, cleanup automation.

## Impact

- **New top-level directory:** `NFCU-session-4/`
- **New OpenSpec capabilities:** nine listed above
- **Affected code:** none (purely additive)
- **Lab engineering lead time required:** content must be ready by June 6, 2026
- **Speaker rehearsal path:** complete end-to-end runnable on `kind` with no AWS dependency
- **Speaker demo path:** EKS cluster provisionable via `terraform apply` against the speaker's own AWS account
- **Compatibility:** Kubernetes 1.34, 1.35, 1.36; KServe 0.16, 0.17
