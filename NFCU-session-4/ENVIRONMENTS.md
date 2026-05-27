# Environments: local kind vs EKS (+ in-cluster canary)

Session 4 has **two target environments** for the same workload, plus a canary rollout
*within* a cluster. There is no dev/staging/production ladder — the choice is **where you
run it**, and both run the identical add-ons and `InferenceService` manifests.

## The two environments

| Environment | What it is | Cloud spend | Bring up / tear down |
|---|---|---|---|
| **local (kind)** | A 3-node `kind` cluster on your laptop running the whole session | **None** | [`cluster/local/up.sh`](cluster/local/) · `down.sh` |
| **EKS** | Your own AWS account, for the live demo or post-session reproduction | ~$40–70 per 8-hour window | [`cluster/eks/up.sh`](cluster/eks/) · `down.sh` (Terraform) |

- **local** is the default path for rehearsal and for attendees without AWS — no spend.
- **EKS** uses the [`cluster/eks/terraform/`](cluster/eks/terraform/) module: EKS module
  `~> 21`, **EKS Pod Identity** (not IRSA), and **Kubernetes 1.35** — the latest version EKS
  offers as of May 2026 (1.36 is the latest upstream GA but EKS does not support it yet).
  **Always tear down** when done.

Both environments install the same add-ons ([`cluster/addons/`](cluster/addons/)): Knative
Serving, Kourier, KServe, OpenCost, Prometheus, Grafana (plus the AWS Load Balancer
Controller on EKS only), and deploy the same KServe `InferenceService` manifests.

## In-cluster rollout: canary

Within whichever cluster you choose, **Lab 4** demonstrates a
[canary rollout with rollback](attendee-guide/lab-4-canary-rollout.md): a new model
revision takes a traffic percentage, is observed, then is promoted to 100% or rolled back.
`InferenceService`s scale to zero when idle.

```
choose environment ─▶ kind (no spend)  ─┐
                      EKS (your AWS)   ─┴▶ install add-ons ─▶ deploy InferenceService
                                                                   │
                                              canary rollout (lab 4): split traffic ─▶ promote / rollback
```

## Labs

Four labs in [`attendee-guide/`](attendee-guide/): deploy an InferenceService, load-test
and autoscale, an LLM-on-CPU with cost attribution, and the canary rollout. The full
session can be rehearsed end-to-end on `kind` via [`rehearsal/`](rehearsal/).

## A note on validation / CI

There is no repository-root workflow for Session 4. Validation ships as a **copy-ready
template** at [`ci/nfcu-session-4-validate.yml`](ci/nfcu-session-4-validate.yml) (GitHub
only runs workflows from the repo root, which this self-contained directory does not own),
and the portable, live entry point is **`make validate`**.
