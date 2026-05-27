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
