# NFCU-session-4 — KServe ML Serving: OpenSpec Change Proposal

> Single-file OpenSpec change proposal for the **add-nfcu-session-4-kserve-collateral** change.
> Paste into Claude Code via `/goal` at the root of `KodeKloudWebinars`.

---

## 0. Goal for Claude Code

You are working in `https://github.com/peopleforrester/KodeKloudWebinars.git`. Existing webinar directories follow the convention `NFCU-session-N/` (e.g., `NFCU-session-1/`, `NFCU-session-2/`, `NFCU-session-3/`). Match their pattern. The non-NFCU `Agentic_DevOps/` directory is tone-and-structure reference for prose style only — declarative, lab-grounded, no marketing language.

Do two things, in order:

1. **Initialize OpenSpec scaffolding** if `openspec/` does not exist. Create `openspec/project.md`, `openspec/specs/`, `openspec/changes/`. Use the `project.md` content in §1 below.
2. **Create the change proposal directory** `openspec/changes/add-nfcu-session-4-kserve-collateral/` with the contents in §§2–4. Then **implement** the change by building out `NFCU-session-4/` per the spec deltas in §5.

**Stack constraints (non-negotiable):**

- Kubernetes 1.34+ (manifests must be valid for 1.34, 1.35, 1.36)
- KServe 0.16+ in **Knative deployment mode** (canary + scale-to-zero require it)
- Knative Serving + Kourier (Gateway API noted as forward-looking but not used in the lab)
- Kubecost OSS / OpenCost for cost attribution
- Prometheus + Grafana for metrics
- Python 3.12+ for the TinyLlama predictor container
- k6 0.57+ for load tests
- CPU-only — no GPU manifests in the active YAML; GPU patterns appear as commented reference blocks only
- Container images: publishable to a configurable registry; default targets `public.ecr.aws/kodekloud-workshop/` but every image build must be fully reproducible against any registry

**In scope (build it):**

- EKS cluster Terraform module for the speaker's demo cluster and for attendees who want to reproduce post-session on their own AWS account
- Cluster add-ons bootstrap (Knative, Kourier, KServe, OpenCost, Prometheus, Grafana) usable on both EKS and local kind
- Per-attendee namespace overlays (kustomize) consumed by the KodeKloud lab platform
- Full local rehearsal path on `kind` so the speaker can dry-run without burning AWS spend

**Out of scope (do not build):**

- The KodeKloud lab platform's per-attendee EKS provisioning workflow (lab platform owns that; we ship overlays it consumes)
- Per-attendee IRSA wiring for 30 attendees (lab platform owns it; we document the pattern in the runbook)
- Sessions 1–3 collateral (referenced but not built here)
- Anything GPU-bound at apply time (vLLM, MIG, GPU operator) — present as commented reference YAML only

---

## 1. `openspec/project.md`

```markdown
# KodeKloudWebinars — OpenSpec Project Context

## Purpose

Practitioner collateral from KodeKloud webinars. Each webinar gets a top-level directory containing the slides reference, attendee-facing docs, lab manifests, demo apps, and a definition-of-done checklist for the lab engineering team.

## Stack

- Documentation: Markdown (prose-driven, narrative voice)
- Lab infrastructure: Kubernetes (1.34+), KServe, Knative, kustomize, Helm
- Cluster provisioning: Terraform (AWS / EKS), kind / k3d for local
- Demo apps: Python 3.12+, FastAPI, k6, kubectl
- Container images: built via Docker / nerdctl, published to public ECR
- Cost attribution: Kubecost OSS / OpenCost

## Conventions

- **Per-webinar directory** at repo root using the `NFCU-session-N/` naming convention for the NFCU engagement (the `Agentic_DevOps/` directory predates this convention and stays as-is).
- **Per-concern subdirectories** within each webinar directory (e.g., `manifests/`, `tests/`, `runbook/`, `reference-card/`, `cluster/`).
- **README at every level.** Each directory explains what's in it and how to use it.
- **No code in markdown** beyond illustrative snippets. Runnable code lives in its own files.
- **Prose voice.** Direct. Declarative. No marketing language. No "exciting." No "leverages." Tone reference: `Agentic_DevOps/90-day-playbook/playbook.md`.
- **Time-budgeted.** Anything attendee-facing names the duration upfront.
- **Failure modes explicit.** Every lab has a troubleshooting matrix.

## OpenSpec Workflow

- Changes live in `openspec/changes/<change-id>/`.
- After implementation, archive the change by moving its `specs/` deltas into `openspec/specs/` as the new current state.
- Each capability spec uses EARS-style SHALL requirements with Given/When/Then scenarios.
```

---

## 2. `openspec/changes/add-nfcu-session-4-kserve-collateral/proposal.md`

```markdown
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
```

---

## 3. `openspec/changes/add-nfcu-session-4-kserve-collateral/tasks.md`

```markdown
# Tasks: add-nfcu-session-4-kserve-collateral

Implementation tasks ordered by dependency. Each top-level task ships in roughly one PR's worth of work.

## 1. Repository scaffolding

- [ ] 1.1 Create `NFCU-session-4/` at repo root
- [ ] 1.2 Create top-level `NFCU-session-4/README.md` with role-based starting points (Platform Engineer / DevOps Engineer / Lab Engineer / Speaker)
- [ ] 1.3 Update root `README.md` to add Session 4 to the "Available Content" section, matching the Agentic_DevOps entry format
- [ ] 1.4 Create `NFCU-session-4/.gitignore` excluding `*.tar.gz`, `model-artifacts/*.bst`, `kubeconfig`, `.env*`, `terraform.tfstate*`, `.terraform/`, `*.tfvars` (but not `*.tfvars.example`)
- [ ] 1.5 Create `NFCU-session-4/Makefile` with targets: `validate`, `bootstrap-local`, `teardown-local`, `eks-up`, `eks-down`, `build-predictor`, `run-rehearsal`, `clean`

## 2. EKS provisioning (nfcu-session-4-eks-cluster)

- [ ] 2.1 Create `NFCU-session-4/cluster/eks/README.md` — prerequisites (AWS account, AWS CLI v2, Terraform 1.10+), cost estimate, day-of procedure, teardown procedure
- [ ] 2.2 Create `NFCU-session-4/cluster/eks/terraform/versions.tf` — pin Terraform ≥1.10, AWS provider ≥5.80, Helm provider ≥2.16, Kubernetes provider ≥2.34
- [ ] 2.3 Create `NFCU-session-4/cluster/eks/terraform/variables.tf` — `region` (default `us-east-1`), `cluster_name` (default `nfcu-session-4`), `kubernetes_version` (default `1.34`), `node_instance_type` (default `m5.xlarge`), `node_desired_size` (default 2), `node_max_size` (default 5), `model_artifacts_bucket_name`
- [ ] 2.4 Create `NFCU-session-4/cluster/eks/terraform/main.tf` — VPC via `terraform-aws-modules/vpc/aws` (3 AZs, public + private subnets), EKS via `terraform-aws-modules/eks/aws` v20+, managed node group, AWS Load Balancer Controller IAM role via IRSA, Cluster Autoscaler IRSA, S3 bucket for model artifacts, IAM role for KServe storage initializer (IRSA)
- [ ] 2.5 Create `NFCU-session-4/cluster/eks/terraform/outputs.tf` — cluster name, cluster endpoint, kubeconfig command, model artifacts bucket name, IRSA role ARNs
- [ ] 2.6 Create `NFCU-session-4/cluster/eks/terraform/terraform.tfvars.example` — annotated example with cost-anchor comment ("estimated $40–$70 for an 8-hour demo + rehearsal")
- [ ] 2.7 Create `NFCU-session-4/cluster/eks/up.sh` — wraps `terraform init`, `terraform plan`, `terraform apply`, prints next-step command for `bootstrap-cluster-addons.sh`
- [ ] 2.8 Create `NFCU-session-4/cluster/eks/down.sh` — wraps `terraform destroy` with safety check requiring the user to type the cluster name
- [ ] 2.9 Verify `terraform validate` passes for the module in CI / make target

## 3. Cluster add-ons (nfcu-session-4-cluster-addons)

- [ ] 3.1 Create `NFCU-session-4/cluster/addons/README.md` — what gets installed, in what order, why
- [ ] 3.2 Create `NFCU-session-4/cluster/addons/bootstrap.sh` — idempotent installer that takes one argument (`eks` or `local`) and installs add-ons in dependency order: cert-manager → Knative Serving → Kourier → KServe → kube-prometheus-stack → OpenCost. On `eks`, additionally installs the AWS Load Balancer Controller before Kourier
- [ ] 3.3 Create `NFCU-session-4/cluster/addons/helm-values/cert-manager.yaml`
- [ ] 3.4 Create `NFCU-session-4/cluster/addons/helm-values/knative-serving.yaml`
- [ ] 3.5 Create `NFCU-session-4/cluster/addons/helm-values/kourier.yaml`
- [ ] 3.6 Create `NFCU-session-4/cluster/addons/helm-values/kserve.yaml` — pinned to 0.16.x; documents the 0.17 upgrade path in a comment
- [ ] 3.7 Create `NFCU-session-4/cluster/addons/helm-values/kube-prometheus-stack.yaml` — minimal config (no Alertmanager, retention 24h)
- [ ] 3.8 Create `NFCU-session-4/cluster/addons/helm-values/opencost.yaml`
- [ ] 3.9 Create `NFCU-session-4/cluster/addons/helm-values/aws-load-balancer-controller.yaml` (EKS only)
- [ ] 3.10 Every Helm values file must have a comment header naming `chartVersion`, `appVersion`, and the upstream chart URL
- [ ] 3.11 Add `NFCU-session-4/cluster/addons/verify.sh` — checks every component reports Ready=True, exits non-zero with the failing component named otherwise

## 4. Local cluster (nfcu-session-4-local-cluster)

- [ ] 4.1 Create `NFCU-session-4/cluster/local/README.md`
- [ ] 4.2 Create `NFCU-session-4/cluster/local/kind-config.yaml` — 3-node cluster (1 control-plane + 2 workers), port mappings for Kourier ingress (80, 443, 31080)
- [ ] 4.3 Create `NFCU-session-4/cluster/local/up.sh` — creates kind cluster + invokes `cluster/addons/bootstrap.sh local`
- [ ] 4.4 Create `NFCU-session-4/cluster/local/down.sh` — destroys kind cluster + removes related Docker artifacts
- [ ] 4.5 Document minimum laptop spec (16 GB RAM, 4+ CPU cores) in the local README

## 5. Per-attendee overlays (nfcu-session-4-lab-overlays)

- [ ] 5.1 Create `NFCU-session-4/cluster/lab-overlays/README.md` — explains the lab platform consumes these; we ship the base + a sample overlay
- [ ] 5.2 Create `NFCU-session-4/cluster/lab-overlays/base/kustomization.yaml`
- [ ] 5.3 Create `NFCU-session-4/cluster/lab-overlays/base/namespace.yaml`
- [ ] 5.4 Create `NFCU-session-4/cluster/lab-overlays/base/resourcequota.yaml` — 4 vCPU, 8 Gi memory, max 10 pods
- [ ] 5.5 Create `NFCU-session-4/cluster/lab-overlays/base/networkpolicy.yaml` — deny cross-namespace
- [ ] 5.6 Create `NFCU-session-4/cluster/lab-overlays/base/serviceaccount.yaml` — with IRSA annotation placeholder
- [ ] 5.7 Create `NFCU-session-4/cluster/lab-overlays/overlays/attendee-sample/kustomization.yaml` — stamps a sample attendee namespace; documents the pattern the lab platform uses to mass-produce these

## 6. Inference service manifests (nfcu-session-4-inferenceservice-manifests)

- [ ] 6.1 Create `NFCU-session-4/manifests/README.md` — index keyed to lab
- [ ] 6.2 Create `NFCU-session-4/manifests/lab1-xgboost-inferenceservice.yaml` — XGBoost v1.0.0, `minReplicas: 0`, `maxReplicas: 5`, `containerConcurrency: 50`. Includes a `# STORAGE OPTIONS:` block in comments showing PVC (local) and S3 (EKS) URI patterns
- [ ] 6.3 Create `NFCU-session-4/manifests/lab2-hpa-baseline-deployment.yaml` — plain Deployment + Service + HPA(CPU 50%, min 1 max 5)
- [ ] 6.4 Create `NFCU-session-4/manifests/lab3-tinyllama-inferenceservice.yaml` — TinyLlama custom predictor, `minReplicas: 0`, `maxReplicas: 3`, `containerConcurrency: 5`, `requests: 4Gi / limits: 6Gi`
- [ ] 6.5 Create `NFCU-session-4/manifests/lab4-xgboost-canary-v1-0-1.yaml` — same name as lab 1, updated storageUri, `canaryTrafficPercent: 10`
- [ ] 6.6 Create `NFCU-session-4/manifests/lab4-xgboost-promote.yaml` — `canaryTrafficPercent` field removed
- [ ] 6.7 Create `NFCU-session-4/manifests/lab4-xgboost-rollback.yaml` — `canaryTrafficPercent: 0`
- [ ] 6.8 Create `NFCU-session-4/manifests/_reference-gpu-vllm.yaml.disabled` — GPU + vLLM reference; the `.disabled` suffix prevents `kubectl apply -f manifests/` from picking it up
- [ ] 6.9 Create `NFCU-session-4/manifests/model-artifacts/README.md`
- [ ] 6.10 Create `NFCU-session-4/manifests/model-artifacts/generate-xgboost-models.py` — deterministic, seeded training of v1.0.0 and v1.0.1 XGBoost models on UCI Adult Census Income. Writes `model-v1.0.0/model.bst` and `model-v1.0.1/model.bst`
- [ ] 6.11 Create `NFCU-session-4/manifests/model-artifacts/upload-to-s3.sh` — uploads generated models to the S3 bucket created by Terraform (reads bucket name from terraform output)
- [ ] 6.12 Verify every active manifest passes `kubectl apply --dry-run=client -f`

## 7. TinyLlama predictor container (nfcu-session-4-tinyllama-predictor-image)

- [ ] 7.1 Create `NFCU-session-4/predictors/tinyllama/README.md`
- [ ] 7.2 Create `NFCU-session-4/predictors/tinyllama/Dockerfile` — multi-stage, multi-arch (linux/amd64, linux/arm64), Python 3.12 slim base, weights downloaded at build time
- [ ] 7.3 Create `NFCU-session-4/predictors/tinyllama/pyproject.toml` — dependencies pinned: `transformers==4.50.*`, `torch==2.5.*` (CPU build), `kserve==0.16.*`, `fastapi==0.115.*`
- [ ] 7.4 Create `NFCU-session-4/predictors/tinyllama/server.py` — KServe `Model` subclass. Input: `{"prompt": str, "max_tokens": int}`. Output: `{"completion": str, "model": str, "tokens_generated": int}`
- [ ] 7.5 Create `NFCU-session-4/predictors/tinyllama/health.py` — liveness + readiness probes
- [ ] 7.6 Create `NFCU-session-4/predictors/tinyllama/distilgpt2-fallback.Dockerfile`
- [ ] 7.7 Create `NFCU-session-4/predictors/tinyllama/build.sh` — wraps `docker buildx` for multi-arch publish; registry configurable via env var, default `public.ecr.aws/kodekloud-workshop/tinyllama-kserve`
- [ ] 7.8 Create `NFCU-session-4/predictors/tinyllama/push-to-ecr.sh` — pushes to a private ECR repo in the speaker's AWS account; created if absent
- [ ] 7.9 Create `NFCU-session-4/predictors/tinyllama/test-local.sh` — runs container, sends a sample completion via curl, asserts non-empty completion
- [ ] 7.10 Add `predictors/tinyllama/.dockerignore`

## 8. Load test harness (nfcu-session-4-load-test-harness)

- [ ] 8.1 Create `NFCU-session-4/tests/README.md`
- [ ] 8.2 Create `NFCU-session-4/tests/smoke/sample-payload-xgboost.json`
- [ ] 8.3 Create `NFCU-session-4/tests/smoke/sample-payload-llm.json` — `{"prompt": "The future of cloud-native ML is", "max_tokens": 50}`
- [ ] 8.4 Create `NFCU-session-4/tests/smoke/curl-tests.sh`
- [ ] 8.5 Create `NFCU-session-4/tests/load/k6-xgboost-kserve.js` — ramp 1→100 VUs over 2 min, hold 3 min, ramp down 1 min; custom metric: requests-per-revision
- [ ] 8.6 Create `NFCU-session-4/tests/load/k6-xgboost-hpa.js` — same ramp against the HPA baseline
- [ ] 8.7 Create `NFCU-session-4/tests/load/k6-tinyllama.js` — gentler ramp (1→10 VUs)
- [ ] 8.8 Create `NFCU-session-4/tests/load/k6-canary-traffic.js` — steady 5 RPS for 5 minutes
- [ ] 8.9 Create `NFCU-session-4/tests/load/compare-scaling.sh` — runs both k6 scripts back-to-back, prints time-to-scale-up, peak pod count, time-to-scale-down

## 9. Attendee collateral (nfcu-session-4-collateral)

- [ ] 9.1 Create `NFCU-session-4/attendee-guide/README.md`
- [ ] 9.2 Create `NFCU-session-4/attendee-guide/prerequisites.md`
- [ ] 9.3 Create `NFCU-session-4/attendee-guide/lab-1-deploy-inferenceservice.md` (12 min walkthrough)
- [ ] 9.4 Create `NFCU-session-4/attendee-guide/lab-2-load-test-and-scaling.md` (12 min walkthrough)
- [ ] 9.5 Create `NFCU-session-4/attendee-guide/lab-3-llm-and-costs.md` (15 min walkthrough)
- [ ] 9.6 Create `NFCU-session-4/attendee-guide/lab-4-canary-rollout.md` (15 min walkthrough)
- [ ] 9.7 Create `NFCU-session-4/attendee-guide/reproduce-on-your-aws-account.md` — points at the EKS Terraform module for attendees wanting to rebuild post-session; cost-anchored
- [ ] 9.8 Create `NFCU-session-4/attendee-guide/post-session-monday-actions.md`
- [ ] 9.9 Create `NFCU-session-4/attendee-guide/faq.md`
- [ ] 9.10 Create `NFCU-session-4/reference-card/kserve-on-k8s.md` — print-friendly reference card

## 10. Operations runbook (nfcu-session-4-operations-runbook)

- [ ] 10.1 Create `NFCU-session-4/runbook/README.md`
- [ ] 10.2 Create `NFCU-session-4/runbook/definition-of-done.md` — five gated checklists with dates: Pre-Provisioning (by 2026-06-02), Per-Attendee Provisioning (by 2026-06-06), Pre-Session Validation (by 2026-06-13), Session Day (2026-06-18), Post-Session
- [ ] 10.3 Create `NFCU-session-4/runbook/troubleshooting-matrix.md` — at least 12 rows covering storage initializer, Pending pods, 503 cold-start, scale-down stuck, k6 errors, LLM OOMKilled, missing Kubecost data, canary not splitting, rollback not restoring, kind networking, helm release conflicts, ImagePullBackOff
- [ ] 10.4 Create `NFCU-session-4/runbook/day-of-operations.md` — T-60 min through T+30 min timeline
- [ ] 10.5 Create `NFCU-session-4/runbook/cleanup-automation.md` — what dies at T+30 min, what persists 24h, what's gone by 2026-06-20
- [ ] 10.6 Create `NFCU-session-4/runbook/dry-run-checklist.md` — for the June 13 end-to-end validation
- [ ] 10.7 Create `NFCU-session-4/runbook/speaker-aws-spend.md` — cost estimates for the speaker's EKS demo cluster (provisioning, idle, under-load, teardown verification)

## 11. Speaker rehearsal path

- [ ] 11.1 Create `NFCU-session-4/rehearsal/README.md`
- [ ] 11.2 Create `NFCU-session-4/rehearsal/run-full-session-local.sh` — kind path: bootstrap, deploy labs 1–4, run all k6 scripts, teardown
- [ ] 11.3 Create `NFCU-session-4/rehearsal/run-full-session-eks.sh` — EKS path: terraform apply, bootstrap add-ons, deploy labs 1–4, run k6 scripts, terraform destroy
- [ ] 11.4 Create `NFCU-session-4/rehearsal/timing-notes.md` — observed step durations on a developer laptop and on EKS

## 12. CI

- [ ] 12.1 Add `.github/workflows/nfcu-session-4-validate.yml` if `.github/workflows/` exists, otherwise rely on the `validate` Makefile target. Validation runs: `kubectl apply --dry-run=client` on every manifest, `yamllint`, `hadolint`, `markdownlint`, `terraform validate`, `terraform fmt -check`
- [ ] 12.2 The Makefile `validate` target runs the same checks locally

## 13. Archive

- [ ] 13.1 After all tasks above pass, move `openspec/changes/add-nfcu-session-4-kserve-collateral/specs/*` to `openspec/specs/*`
- [ ] 13.2 Delete the `changes/add-nfcu-session-4-kserve-collateral/` directory after archival
```

---

## 4. `openspec/changes/add-nfcu-session-4-kserve-collateral/design.md`

```markdown
# Design: add-nfcu-session-4-kserve-collateral

## Context

Session 4 of a four-part NFCU webinar series. Sessions 1–3 are SageMaker-flavored. Session 4 moves the same workload to Kubernetes-native serving on KServe. Live workshop, 25–30 attendees, June 18, 2026.

This is the first webinar entry in the repo with runnable infrastructure (Terraform, manifests, container images, scripts) in addition to docs. Decisions made here become the template for future infrastructure-heavy webinars.

Three audiences for the same artifacts:
1. **Speaker** — needs a personally-owned EKS demo cluster for the live session and a local kind path for rehearsal
2. **Lab engineering team** — needs manifests, container images, k6 scripts, and a Definition-of-Done they can sign off against by June 6
3. **Attendees** — need durable collateral they can re-run the week after the session, either on the lab platform (during the 24-hour catch-up window) or on their own AWS account post-session

## Goals

- Speaker can rehearse the entire session end-to-end on a laptop in under 30 minutes (no AWS spend)
- Speaker can `terraform apply` an EKS demo cluster in under 25 minutes, then bootstrap add-ons and labs in under 15 minutes
- Lab engineering team has a Definition-of-Done they sign off against by June 6
- Manifests are valid for Kubernetes 1.34, 1.35, 1.36
- Total per-attendee cluster cost ≤ $1.60 (session doc target)
- Speaker's own EKS demo cluster costs ≤ $70 for an 8-hour rehearsal-plus-session window

## Non-Goals

- Real GPU serving. CPU-only at apply time; GPU reference YAML is `.disabled`.
- vLLM in the runtime path. Roadmap-only.
- The KodeKloud lab platform's per-attendee EKS provisioning workflow. We ship the kustomize overlays it consumes.
- Sessions 1–3 retrofitting.

## Key Decisions

### Two cluster paths: kind for rehearsal, EKS for demo

The speaker runs the live session against a personally-owned EKS cluster (Terraform-provisioned in `cluster/eks/terraform/`). The same speaker rehearses against a local kind cluster (`cluster/local/`). Both share the same add-ons bootstrap (`cluster/addons/bootstrap.sh`) and the same lab manifests.

Tradeoff: maintaining two cluster paths is more work, but it lets the speaker iterate without burning AWS spend and gives attendees a no-AWS reproduction path. The shared add-ons script keeps the second path nearly free to maintain.

### EKS via terraform-aws-modules, not raw resources

The `terraform-aws-modules/eks/aws` module is the de facto community standard. Using it means the Terraform stays ~200 lines instead of ~2000. The cost is module-pinning discipline: we pin to a specific major version and document upgrade paths.

### IRSA for KServe storage initializer

The S3 bucket holding model artifacts is private. The KServe storage initializer needs to read from it. IRSA (IAM Roles for Service Accounts) is the right pattern: the ServiceAccount in each attendee namespace is annotated with an IAM role ARN, the storage initializer assumes that role, and reads the bucket without long-lived credentials. The Terraform provisions both the role and the trust relationship to OIDC.

### Knative deployment mode, not Standard

KServe supports two deployment modes. Knative gives concurrency-based autoscaling, scale-to-zero, and `canaryTrafficPercent`. Standard loses all three. The session teaches all three. Knative is required.

### Kourier, not Istio or Gateway API

Kourier is the simplest Knative network layer. Istio adds 30+ minutes to cluster bootstrap and brings service-mesh complexity that's irrelevant to the session. Gateway API is forward-looking and called out in the FAQ. For lab simplicity, Kourier wins. On EKS, Kourier sits behind an NLB provisioned by the AWS Load Balancer Controller.

### TinyLlama, not a "real" LLM

The lab cluster is CPU-only. TinyLlama 1.1B runs on CPU with 4–6 Gi RAM and produces output coherent enough for the cost-attribution exercise. distilGPT-2 is the fallback if HuggingFace rate-limits the download on session day.

### Custom predictor container, not the HuggingFace runtime

KServe's HuggingFace runtime defaults to vLLM (GPU). Falling back to its transformers mode would work, but a custom predictor gives us full control over the input/output schema (matches the curl examples in the attendee guide), a smaller image, and identical Dockerfile structure between TinyLlama and distilGPT-2 fallback. Cost: ~150 lines of Python we own.

### Model artifact generation script, not pre-built artifacts

Storing `.bst` files in git is wrong. `generate-xgboost-models.py` produces v1.0.0 and v1.0.1 on demand, deterministically. `upload-to-s3.sh` then writes them into the S3 bucket Terraform created. Re-running with the same seed produces byte-identical files.

### `.disabled` filename suffix for GPU reference

Naming a file `_reference-gpu-vllm.yaml.disabled` makes it invisible to `kubectl apply -f .` while keeping it discoverable. Cheapest way to ship reference material without footgun risk.

## Risks

- **HuggingFace rate-limit or outage on session day** → distilGPT-2 fallback image, pre-pulled to nodes; runbook makes pre-pull a hard DoD item
- **EKS cluster autoscaler lag under load** → Terraform configures Cluster Autoscaler with aggressive scale-up; runbook covers manual node-group scale-up as a fallback
- **Kind cluster runs out of memory loading TinyLlama on <16 Gi laptops** → minimum spec documented; distilGPT-2 path available
- **KServe 0.17 lands with breaking changes between authoring and June 18** → Helm values pinned to 0.16.x; 0.17 upgrade tracked as a follow-up change
- **Speaker forgets to `terraform destroy`** → `down.sh` is in the runbook's post-session checklist; `cost-estimate` Make target prints the running burn rate

## Open Questions

- Should the EKS module use Karpenter or Cluster Autoscaler? **Decision: Cluster Autoscaler** for simplicity and predictability over a 2-hour demo. Karpenter is the production choice but its node-launch behavior is harder to predict in a live demo.
- Should the speaker's S3 bucket be public-read for attendees to reproduce, or do attendees re-generate models on their own account? **Decision: attendees regenerate.** Public buckets are a footgun and the generation script is deterministic.
```

---

## 5. Capability spec deltas

Each subsection is the contents of `openspec/changes/add-nfcu-session-4-kserve-collateral/specs/<capability>/spec.md`.

### 5.1 `nfcu-session-4-collateral/spec.md`

```markdown
# nfcu-session-4-collateral

## ADDED Requirements

### Requirement: NFCU-session-4 directory exists at repo root

The repository SHALL contain a top-level directory `NFCU-session-4/` matching the `NFCU-session-N/` convention used by other sessions in the series.

#### Scenario: Directory follows naming convention
- **GIVEN** a fresh clone of the repository
- **WHEN** the user lists the repo root
- **THEN** `NFCU-session-4/` is present
- **AND** its README documents the per-subdirectory contents

### Requirement: Root README links Session 4

The root `README.md` SHALL list Session 4 under "Available Content" with the session title, date (June 18, 2026), and a one-paragraph description.

#### Scenario: Reader finds Session 4 from the repo root
- **GIVEN** a reader on the root README
- **WHEN** they scan "Available Content"
- **THEN** they see a Session 4 entry linking to `NFCU-session-4/README.md`

### Requirement: Per-lab attendee walkthroughs

`attendee-guide/` SHALL contain one markdown walkthrough per lab (1, 2, 3, 4), each with prerequisites, step-by-step instructions, success criteria, and time budget.

#### Scenario: Attendee re-runs a lab post-session
- **GIVEN** an attendee 7 days after the live session
- **WHEN** they open any lab walkthrough
- **THEN** the kubectl commands, expected outputs, and pass criteria are sufficient to complete the lab without the recording

### Requirement: Self-service reproduction path is documented

`attendee-guide/reproduce-on-your-aws-account.md` SHALL document how an attendee reproduces the entire session on their own AWS account using the EKS Terraform module.

#### Scenario: Attendee reproduces without lab platform access
- **GIVEN** an attendee with their own AWS account and Terraform installed
- **WHEN** they follow `reproduce-on-your-aws-account.md`
- **THEN** they end up with a working KServe cluster running labs 1–4
- **AND** the document includes a cost estimate before they apply

### Requirement: Reference card is print-friendly

`reference-card/kserve-on-k8s.md` SHALL summarize KServe primitives, deployment modes, GPU cost levers, and canary vs shadow decision in one printed letter-size page.

#### Scenario: Reference card renders cleanly
- **GIVEN** the reference card markdown
- **WHEN** rendered via pandoc with 0.5-inch margins
- **THEN** the PDF is exactly 1 page with no content cut off
```

### 5.2 `nfcu-session-4-eks-cluster/spec.md`

```markdown
# nfcu-session-4-eks-cluster

## ADDED Requirements

### Requirement: Terraform module provisions a working EKS cluster

`cluster/eks/terraform/` SHALL contain a Terraform module that provisions an EKS cluster suitable for running labs 1–4 with one `terraform apply`.

#### Scenario: Speaker provisions cluster from cold
- **GIVEN** an AWS account with appropriate IAM permissions, Terraform ≥1.10 installed, and the example tfvars copied to `terraform.tfvars`
- **WHEN** the speaker runs `cd cluster/eks && bash up.sh`
- **THEN** within 25 minutes the EKS cluster reports ACTIVE
- **AND** the node group is `Active` with desired capacity
- **AND** `outputs.tf` produces a working `aws eks update-kubeconfig` command

### Requirement: Cluster sizing is appropriate for the demo

The default node group SHALL run `m5.xlarge` instances with `desired_size=2` and `max_size=5`.

#### Scenario: Default sizing supports labs 1–4
- **GIVEN** the cluster is provisioned with default tfvars
- **WHEN** all four lab manifests are applied and traffic is generated
- **THEN** the cluster autoscaler scales node count as needed
- **AND** no pod is stuck Pending due to resource pressure for more than 5 minutes

### Requirement: IRSA roles support KServe storage and AWS Load Balancer Controller

Terraform SHALL provision IAM-roles-for-service-accounts (IRSA) for the KServe storage initializer (reading model artifacts from S3), the AWS Load Balancer Controller, and the Cluster Autoscaler.

#### Scenario: KServe pulls models from S3 without static credentials
- **GIVEN** an InferenceService with a `s3://` storageUri pointing at the Terraform-managed bucket
- **WHEN** the InferenceService is applied
- **THEN** the storage initializer succeeds without any AWS access keys in the cluster
- **AND** the model is downloaded to the predictor pod

### Requirement: S3 bucket for model artifacts is created

Terraform SHALL provision an S3 bucket whose name is exposed via outputs, intended to hold the v1.0.0 and v1.0.1 XGBoost model artifacts.

#### Scenario: Models are uploaded to S3 from terraform output
- **GIVEN** the cluster is provisioned
- **WHEN** the speaker runs `bash manifests/model-artifacts/upload-to-s3.sh`
- **THEN** the script reads the bucket name from `terraform output -raw model_artifacts_bucket_name`
- **AND** both model versions are uploaded to the expected S3 keys

### Requirement: Teardown is destructive and safety-gated

`cluster/eks/down.sh` SHALL fully destroy the cluster but require the user to type the cluster name as confirmation.

#### Scenario: Accidental teardown is prevented
- **GIVEN** the user runs `bash cluster/eks/down.sh`
- **WHEN** they do not type the exact cluster name
- **THEN** the script exits without invoking `terraform destroy`

#### Scenario: Confirmed teardown completes cleanly
- **GIVEN** the user runs `bash cluster/eks/down.sh` and types the cluster name correctly
- **WHEN** Terraform destroy completes
- **THEN** no AWS resources from the module remain
- **AND** the next `aws eks list-clusters` does not list the cluster

### Requirement: Cost estimate is anchored in the runbook

`runbook/speaker-aws-spend.md` SHALL document the expected cost of an 8-hour rehearsal-plus-session window with default sizing.

#### Scenario: Speaker knows what to expect on the AWS bill
- **GIVEN** the speaker reads the spend doc before provisioning
- **WHEN** they finish reading
- **THEN** they have a concrete dollar range and the line-item breakdown (EKS control plane, node hours, NLB, EBS, NAT gateway)
```

### 5.3 `nfcu-session-4-cluster-addons/spec.md`

```markdown
# nfcu-session-4-cluster-addons

## ADDED Requirements

### Requirement: Add-ons bootstrap is idempotent and ordered

`cluster/addons/bootstrap.sh` SHALL install cert-manager, Knative Serving, Kourier, KServe, kube-prometheus-stack, and OpenCost in dependency order. On EKS it additionally installs the AWS Load Balancer Controller before Kourier.

#### Scenario: Bootstrap completes against a fresh cluster
- **GIVEN** an empty cluster (kind or EKS) with kubectl context set
- **WHEN** the user runs `bash cluster/addons/bootstrap.sh eks` or `bash cluster/addons/bootstrap.sh local`
- **THEN** every component reaches Ready=True
- **AND** the script exits 0

#### Scenario: Re-running is a no-op
- **GIVEN** a cluster where bootstrap has already completed
- **WHEN** the user re-runs the same command
- **THEN** no changes are applied
- **AND** the script exits 0

#### Scenario: Failure points at the failing component
- **GIVEN** a component cannot reach Ready within its timeout
- **WHEN** the timeout fires
- **THEN** the script exits non-zero
- **AND** the error message names the failing component
- **AND** dependent components are not installed

### Requirement: All Helm charts are version-pinned

Every helm values file SHALL include a comment header naming the `chartVersion`, `appVersion`, and upstream chart URL.

#### Scenario: Version drift is detectable
- **GIVEN** any helm values file
- **WHEN** a reviewer reads it
- **THEN** the chart version and app version are stated in the header
- **AND** no version is declared in any other location

### Requirement: Verification script gates lab work

`cluster/addons/verify.sh` SHALL check every component reports Ready=True and exit non-zero if any do not.

#### Scenario: Verify catches a partial install
- **GIVEN** an environment where Kourier is healthy but KServe is not
- **WHEN** the user runs verify.sh
- **THEN** the exit code is non-zero
- **AND** KServe is named as the failing component
```

### 5.4 `nfcu-session-4-local-cluster/spec.md`

```markdown
# nfcu-session-4-local-cluster

## ADDED Requirements

### Requirement: Local kind cluster supports the full session

`cluster/local/up.sh` SHALL create a kind cluster sufficient to run labs 1–4 (XGBoost + TinyLlama on CPU) on a developer laptop.

#### Scenario: Speaker rehearses on laptop
- **GIVEN** a laptop with Docker, kubectl, helm, kind, and 16 Gi RAM
- **WHEN** the speaker runs `bash cluster/local/up.sh`
- **THEN** within 15 minutes a 3-node kind cluster is ready with all add-ons
- **AND** the same lab manifests apply against it as against the EKS cluster

### Requirement: Local teardown is complete

`cluster/local/down.sh` SHALL destroy the kind cluster and remove related Docker artifacts.

#### Scenario: Clean slate after teardown
- **GIVEN** a kind cluster created by up.sh
- **WHEN** the user runs `bash cluster/local/down.sh`
- **THEN** `kind get clusters` does not list the cluster
- **AND** no related Docker containers or networks remain
```

### 5.5 `nfcu-session-4-lab-overlays/spec.md`

```markdown
# nfcu-session-4-lab-overlays

## ADDED Requirements

### Requirement: Per-attendee namespace isolation via kustomize base

`cluster/lab-overlays/base/` SHALL define a kustomize base producing a Namespace, ResourceQuota (4 vCPU / 8 Gi memory / 10 pods), NetworkPolicy denying cross-namespace traffic, and a ServiceAccount with IRSA annotation placeholder.

#### Scenario: Attendee namespace cannot exhaust shared cluster
- **GIVEN** a per-attendee namespace stamped from the base
- **WHEN** the attendee tries to exceed 4 vCPU, 8 Gi memory, or 10 pods
- **THEN** the API rejects with a ResourceQuota error naming the exceeded quota

#### Scenario: Cross-namespace traffic is blocked
- **GIVEN** two attendee namespaces from the same base
- **WHEN** a pod in namespace A reaches for a service in namespace B
- **THEN** the connection is dropped by NetworkPolicy

### Requirement: Sample overlay documents stamping pattern

`cluster/lab-overlays/overlays/attendee-sample/` SHALL contain a complete sample overlay that the KodeKloud lab platform replicates per attendee.

#### Scenario: Lab platform integration is clear
- **GIVEN** a lab engineer reading the overlays directory
- **WHEN** they read the sample overlay's kustomization.yaml
- **THEN** they understand how to stamp 30 attendee namespaces (e.g., via a templating loop)
```

### 5.6 `nfcu-session-4-inferenceservice-manifests/spec.md`

```markdown
# nfcu-session-4-inferenceservice-manifests

## ADDED Requirements

### Requirement: Lab 1 manifest deploys XGBoost via KServe

`manifests/lab1-xgboost-inferenceservice.yaml` SHALL deploy XGBoost v1.0.0 in Knative deployment mode with `minReplicas: 0`, `maxReplicas: 5`, `containerConcurrency: 50`.

#### Scenario: Manifest applies cleanly
- **GIVEN** a cluster with KServe 0.16+ and the v1.0.0 model artifact accessible
- **WHEN** the user runs `kubectl apply -f manifests/lab1-xgboost-inferenceservice.yaml -n <namespace>`
- **THEN** within 90 seconds the InferenceService is READY
- **AND** a prediction request returns the expected schema

#### Scenario: Scale-to-zero works after idle
- **GIVEN** a deployed Lab 1 InferenceService with no traffic
- **WHEN** 60 seconds pass with no requests
- **THEN** the predictor pod count drops to 0

### Requirement: Lab 2 HPA baseline demonstrates the anti-pattern

`manifests/lab2-hpa-baseline-deployment.yaml` SHALL deploy the same XGBoost model as a plain Deployment with a CPU-based HPA, used as the "wrong way" comparison in Lab 2.

#### Scenario: HPA scales on CPU, not concurrency
- **GIVEN** the HPA baseline under k6 load
- **WHEN** request volume rises faster than CPU
- **THEN** HPA does not scale up until CPU crosses its threshold
- **AND** the lag is observable and contrasts with the KServe behavior

### Requirement: Lab 3 deploys TinyLlama on CPU

`manifests/lab3-tinyllama-inferenceservice.yaml` SHALL deploy the custom TinyLlama predictor with `minReplicas: 0`, `maxReplicas: 3`, `containerConcurrency: 5`, memory `requests: 4Gi / limits: 6Gi`, no GPU resources requested.

#### Scenario: LLM endpoint comes up
- **GIVEN** a cluster with the TinyLlama image pre-pulled
- **WHEN** the lab 3 manifest is applied
- **THEN** within 120 seconds the InferenceService is READY
- **AND** a completion request returns a non-empty `completion` field

### Requirement: Lab 4 canary uses canaryTrafficPercent

`manifests/lab4-xgboost-canary-v1-0-1.yaml` SHALL update the same `adult-income-classifier` InferenceService's storageUri to v1.0.1 and add `canaryTrafficPercent: 10`.

#### Scenario: Traffic split is observable
- **GIVEN** Lab 1's InferenceService is running v1.0.0
- **WHEN** the canary manifest is applied
- **THEN** ~10% of requests go to v1.0.1 and ~90% to v1.0.0

#### Scenario: Promotion via field removal
- **GIVEN** a canary at 10% to v1.0.1
- **WHEN** `lab4-xgboost-promote.yaml` (no canaryTrafficPercent) is applied
- **THEN** 100% of traffic goes to v1.0.1
- **AND** v1.0.0 remains as previous good revision

#### Scenario: Rollback pins to previous revision
- **GIVEN** a canary at any percentage to v1.0.1
- **WHEN** `lab4-xgboost-rollback.yaml` (canaryTrafficPercent: 0) is applied
- **THEN** 100% of traffic returns to v1.0.0
- **AND** no pod restart occurs

### Requirement: GPU reference YAML is non-applicable

`_reference-gpu-vllm.yaml.disabled` SHALL contain a complete GPU + vLLM reference manifest but SHALL NOT be applicable via `kubectl apply -f manifests/`.

#### Scenario: Bulk apply skips the reference file
- **GIVEN** the manifests directory
- **WHEN** `kubectl apply -f manifests/` runs
- **THEN** the `.disabled` file is ignored
- **AND** no GPU resources are requested

### Requirement: Model artifacts are generated, not committed

`manifests/model-artifacts/generate-xgboost-models.py` SHALL produce both v1.0.0 and v1.0.1 deterministically from UCI Adult Census Income.

#### Scenario: Models are reproducible
- **GIVEN** Python 3.12+ with xgboost, pandas, scikit-learn
- **WHEN** the user runs the generation script
- **THEN** `model-v1.0.0/model.bst` and `model-v1.0.1/model.bst` are produced
- **AND** the same seed produces byte-identical files

#### Scenario: Models upload to S3 from Terraform output
- **GIVEN** the EKS cluster is provisioned
- **WHEN** the user runs `bash manifests/model-artifacts/upload-to-s3.sh`
- **THEN** the script reads the bucket name from `terraform output`
- **AND** both models are uploaded to the expected keys
```

### 5.7 `nfcu-session-4-tinyllama-predictor-image/spec.md`

```markdown
# nfcu-session-4-tinyllama-predictor-image

## ADDED Requirements

### Requirement: Predictor implements KServe Model interface

`predictors/tinyllama/server.py` SHALL subclass `kserve.Model` and implement `load()` and `predict()`.

#### Scenario: Predictor handles standard KServe requests
- **GIVEN** the container running on port 8080
- **WHEN** a POST hits `/v1/models/tinyllama-completion:predict` with `{"prompt": "...", "max_tokens": 50}`
- **THEN** the response is `{"completion": str, "model": "tinyllama-1.1b", "tokens_generated": N}` where N ≤ 50
- **AND** status is 200

#### Scenario: Readiness gates on weight loading
- **GIVEN** the container just started
- **WHEN** Kubernetes probes readiness
- **THEN** the probe fails until weights are loaded
- **AND** subsequent probes return 200

### Requirement: Image is multi-arch and reproducible

The TinyLlama image SHALL be built for `linux/amd64` and `linux/arm64` from a single Dockerfile via `docker buildx`.

#### Scenario: Build script produces both architectures
- **GIVEN** Docker with buildx and qemu
- **WHEN** the user runs `bash predictors/tinyllama/build.sh`
- **THEN** a multi-arch manifest is produced for both platforms

#### Scenario: Image runs on Apple Silicon without emulation
- **GIVEN** an M-series Mac
- **WHEN** the user runs the image via `docker run`
- **THEN** the container starts in under 30 seconds with no qemu translation

### Requirement: distilGPT-2 fallback exists

`predictors/tinyllama/distilgpt2-fallback.Dockerfile` SHALL produce an interchangeable image using distilGPT-2 weights.

#### Scenario: Fallback is drop-in compatible
- **GIVEN** a lab 3 manifest pointing at the fallback image
- **WHEN** the InferenceService is applied
- **THEN** the same request/response contract holds

### Requirement: Push targets a configurable registry

`predictors/tinyllama/build.sh` SHALL accept a registry override via environment variable.

#### Scenario: Speaker pushes to their own ECR
- **GIVEN** the speaker's AWS account and `REGISTRY=<their-ecr-uri>` env var
- **WHEN** they run `bash push-to-ecr.sh`
- **THEN** the image is built and pushed to the speaker's ECR (created if absent)
- **AND** the resulting URI is printed for use in the lab 3 manifest
```

### 5.8 `nfcu-session-4-load-test-harness/spec.md`

```markdown
# nfcu-session-4-load-test-harness

## ADDED Requirements

### Requirement: k6 scripts cover each lab's traffic pattern

`tests/load/` SHALL contain `k6-xgboost-kserve.js`, `k6-xgboost-hpa.js`, `k6-tinyllama.js`, `k6-canary-traffic.js`.

#### Scenario: KServe load drives concurrency-based scaling
- **GIVEN** a deployed Lab 1 InferenceService
- **WHEN** `k6 run tests/load/k6-xgboost-kserve.js` runs
- **THEN** it ramps 1→100 VUs over 2 min, holds 3 min, ramps down 1 min
- **AND** observable pod count rises during hold

#### Scenario: HPA comparison surfaces the autoscaling gap
- **GIVEN** the HPA baseline Deployment running
- **WHEN** the HPA k6 script runs with the same ramp
- **THEN** `tests/load/compare-scaling.sh` prints a side-by-side summary of time-to-scale-up and peak pod count

### Requirement: LLM load test respects concurrency limits

`k6-tinyllama.js` SHALL use a gentler ramp (1→10 VUs) that does not exceed `containerConcurrency: 5` × `maxReplicas: 3`.

#### Scenario: LLM load stays under sustained 5xx
- **GIVEN** the TinyLlama InferenceService at maxReplicas: 3
- **WHEN** the LLM k6 script runs
- **THEN** error rate stays under 1% during steady-state

### Requirement: Canary script supports statistical split observation

`k6-canary-traffic.js` SHALL drive 5 RPS for 5 minutes — enough to observe the split, not enough to trigger autoscaling beyond minReplicas.

#### Scenario: Split is statistically observable
- **GIVEN** a canary at 10% to v1.0.1
- **WHEN** the canary traffic script completes
- **THEN** 8–12% of requests landed on v1.0.1
- **AND** per-revision counts appear in the k6 summary

### Requirement: Smoke tests precede load tests

`tests/smoke/curl-tests.sh` SHALL send one successful prediction to each endpoint before any load test.

#### Scenario: Smoke catches deploy failures fast
- **GIVEN** a deployed InferenceService
- **WHEN** smoke runs
- **THEN** within 5 seconds either all endpoints return 200, or the script exits non-zero naming the failed endpoint
```

### 5.9 `nfcu-session-4-operations-runbook/spec.md`

```markdown
# nfcu-session-4-operations-runbook

## ADDED Requirements

### Requirement: Definition-of-Done has dated gates

`runbook/definition-of-done.md` SHALL contain five gated checklists with explicit calendar dates: Pre-Provisioning (by 2026-06-02), Per-Attendee Provisioning (by 2026-06-06), Pre-Session Validation (by 2026-06-13), Session Day (2026-06-18), Post-Session.

#### Scenario: Lab engineer signs off mechanically
- **GIVEN** a lab engineer working through DoD
- **WHEN** they reach a gate's date
- **THEN** every checkbox is binary (done / not done) with no ambiguity
- **AND** any "not done" item blocks session day

### Requirement: Troubleshooting matrix is exhaustive for known failure modes

`runbook/troubleshooting-matrix.md` SHALL contain at least 12 rows covering: storage initializer failures, Pending pods, 503 cold-start, scale-down stuck, k6 errors, LLM OOMKilled, missing Kubecost data, canary not splitting, rollback not restoring, kind networking, helm release name conflicts, ImagePullBackOff.

#### Scenario: Engineer resolves a known symptom in under 5 minutes
- **GIVEN** an attendee reports a known symptom
- **WHEN** the engineer consults the matrix
- **THEN** they find symptom, likely cause, exact remediation command, and a "how to confirm it worked" step

### Requirement: Day-of-operations timeline covers T-60 to T+30

`runbook/day-of-operations.md` SHALL specify operations from T-60 minutes through T+30 minutes for session start (2026-06-18 10:00 AM ET).

#### Scenario: Lab engineer follows timeline without improvisation
- **GIVEN** the day-of doc at any T-N minute entry
- **WHEN** they read it
- **THEN** they know which command to run, which dashboard to check, which Slack channel to message

### Requirement: Cleanup automation has retention rules

`runbook/cleanup-automation.md` SHALL specify what is destroyed within 30 minutes post-session, what persists 24 hours for catch-up labs, and what is fully decommissioned by 2026-06-20.

#### Scenario: Catch-up labs work for 24 hours
- **GIVEN** an attendee returning 12 hours post-session
- **WHEN** they reconnect
- **THEN** their namespace still has all manifests they applied
- **AND** they can complete labs without re-provisioning

#### Scenario: Cluster is fully gone by June 20
- **GIVEN** the cluster persisted 24 hours post-session
- **WHEN** 48 hours have elapsed
- **THEN** no AWS resources from the session remain billable
- **AND** the cleanup is verifiable from automation logs

### Requirement: Speaker AWS spend is anchored in writing

`runbook/speaker-aws-spend.md` SHALL document expected costs for an 8-hour rehearsal-plus-session window with default Terraform sizing.

#### Scenario: Speaker knows what their AWS bill will be
- **GIVEN** the speaker reads the spend doc before `terraform apply`
- **WHEN** they finish
- **THEN** they have a concrete dollar range and a line-item breakdown (EKS control plane, node hours, NLB, EBS, NAT gateway)

### Requirement: Dry-run checklist precedes session day

`runbook/dry-run-checklist.md` SHALL define the end-to-end validation that must complete by 2026-06-13.

#### Scenario: Dry run catches issues before attendees arrive
- **GIVEN** the dry-run checklist
- **WHEN** the lab engineer executes every step against the provisioned cluster
- **THEN** any failure is logged and triaged against the troubleshooting matrix
- **AND** all blocking issues are resolved before 2026-06-18
```

---

## 6. Acceptance for Claude Code

The change is "implemented" (ready for archival per task 13.1) when:

- All 13 task groups in §3 are checked off
- Every manifest passes `kubectl apply --dry-run=client`
- Every Terraform module passes `terraform validate` and `terraform fmt -check`
- `bash NFCU-session-4/cluster/local/up.sh` succeeds end-to-end on a fresh kind cluster
- `bash NFCU-session-4/rehearsal/run-full-session-local.sh` succeeds end-to-end (cold start to teardown) in under 30 minutes
- `make -C NFCU-session-4 validate` passes
- All nine capability spec deltas have their scenarios satisfied by the implementation
- The root `README.md` lists Session 4 alongside Agentic_DevOps
- No file in `NFCU-session-4/` requires GPU resources at apply time

When all the above hold, move the `specs/` contents into `openspec/specs/` and delete the `changes/add-nfcu-session-4-kserve-collateral/` directory.

---

## 7. Notes for the maintainer (Michael)

- The two cluster paths (EKS + local kind) share the same `cluster/addons/bootstrap.sh`. If one drifts, the rehearsal stops being faithful. Keep the bootstrap script as the single source of add-on truth.
- The `.disabled` suffix on the GPU reference manifest is intentional. Don't rename it without re-checking the bulk-apply behavior.
- The model artifact generator is deterministic (seeded) so the curl examples in `attendee-guide/` stay accurate. If you regenerate models with a different seed, regenerate the curl outputs too.
- `terraform destroy` is a manual step. Put it on the post-session checklist where you actually look — the `runbook/cleanup-automation.md` and the Definition-of-Done's Post-Session gate both reference it. Belt and suspenders.
- KServe 0.17 may ship between now and June 18. The Helm values pin to 0.16.x explicitly. If 0.17 is needed, file a follow-up change (`upgrade-kserve-to-0-17`); don't mutate this one mid-flight.
- Hugging Face download for TinyLlama at image build is the single most fragile thing. Build and pre-pull both TinyLlama and distilGPT-2 images to your demo nodes before T-60. The runbook's Pre-Session Validation gate (June 13) makes this a hard check.
- The Terraform module uses Cluster Autoscaler, not Karpenter. Karpenter is better in production but its node-launch behavior is harder to predict in a live 2-hour demo. If you want to swap to Karpenter later, that's a separate change.
