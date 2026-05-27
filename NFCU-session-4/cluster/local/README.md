# Local kind Cluster (Rehearsal Path)

A 3-node [kind](https://kind.sigs.k8s.io/) cluster that runs the entire session — XGBoost
and TinyLlama on CPU — with **no AWS spend**. This is how the speaker rehearses, and how
anyone without an AWS account can work the labs.

It shares `../addons/bootstrap.sh` with the EKS path, so what you rehearse here is what
runs on demo day. The only differences: no AWS Load Balancer Controller (kind has no NLB),
and Kourier is exposed via NodePort instead of an NLB.

## Minimum laptop spec

| Resource | Minimum | Why |
|---|---|---|
| RAM | **16 GB** | TinyLlama 1.1B needs 4–6 GB; the add-on stack and 3 kind nodes need the rest. On <16 GB, use the distilGPT-2 fallback image (see `predictors/tinyllama/`). |
| CPU | **4+ cores** | KServe + Knative + Prometheus controllers, plus model inference. |
| Disk | ~20 GB free | Container images (KServe, Knative, predictor, Prometheus). |
| Docker | Running, ≥ 8 GB memory limit | kind runs nodes as containers. On Docker Desktop, raise the memory limit in Settings → Resources. |

Required tools: `docker`, `kind` ≥ 0.24, `kubectl` ≥ 1.30, `helm` ≥ 3.14.

## Usage

```bash
bash up.sh      # create the cluster + install all add-ons (~10-15 min first run)
bash down.sh    # delete the cluster and its Docker containers
```

`up.sh` is idempotent: if the `nfcu-session-4` cluster already exists it reuses it and
just re-runs the add-ons bootstrap.

## Networking

The control-plane node maps three host ports (see `kind-config.yaml`):

| Host port | Purpose |
|---|---|
| `31080` | Kourier NodePort — the ingress the labs curl against (`http://localhost:31080`) |
| `80` / `443` | Convenience mappings for HTTP/HTTPS |

`bootstrap.sh local` patches the Kourier Service to NodePort `31080` so it lines up with
the port mapping above.

## What this cannot show

The EKS-only pieces: the AWS Load Balancer Controller, Pod Identity-based S3 model loading, and
the Cluster Autoscaler scaling real EC2 nodes. Those are demonstrated on the EKS path
(`../eks/`). Locally, model artifacts load from a PVC instead of S3 (see the storage
options comment in `manifests/lab1-xgboost-inferenceservice.yaml`).
