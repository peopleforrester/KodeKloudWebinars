# Cluster Add-ons

The shared add-on layer for both cluster paths. `bootstrap.sh` installs the same stack on
EKS and on local kind, so the speaker's rehearsal is faithful to the live demo. This script
is the single source of add-on truth — if it drifts, the two paths diverge.

## Usage

```bash
bash bootstrap.sh local   # kind rehearsal
bash bootstrap.sh eks     # live EKS demo (reads IRSA ARNs from terraform output)

bash verify.sh            # gate before lab work — non-zero exit names the failing add-on
```

Both scripts are idempotent: re-running `bootstrap.sh` is a no-op when everything is already
at the pinned version (`helm upgrade --install` and `kubectl apply` converge).

## Install order and why

| # | Component | Why it's here, in this order |
|---|---|---|
| 1 | **cert-manager** | KServe's admission webhooks need TLS certs; must exist first. |
| 2 | **Knative Serving** | Provides the serverless runtime: scale-to-zero, concurrency autoscaling, revisions. |
| 3 | **AWS Load Balancer Controller** *(EKS only)* | Provisions the NLB that fronts Kourier. Installed before Kourier so the LB exists when Kourier's `LoadBalancer` Service appears. Skipped on kind. |
| 4 | **Kourier** | Knative's network layer (no service mesh). Patched to NodePort 31080 on kind. |
| 5 | **KServe** | The serving controller. Pinned to Knative deployment mode. CRDs install first (`kserve-crd`), then the controller (`kserve-resources`). |
| 6 | **kube-prometheus-stack** | Prometheus + Grafana. No Alertmanager; 24h retention. |
| 7 | **OpenCost** | Per-model cost attribution (Lab 3), wired to the in-cluster Prometheus. |

## Pinned versions

Versions live in two places that must agree: the `*_VERSION` variables at the top of
`bootstrap.sh`, and the header comment in each `helm-values/*.yaml`.

| Component | Version | Source |
|---|---|---|
| cert-manager | `v1.16.1` | `charts.jetstack.io` |
| Knative Serving | `knative-v1.15.2` | github.com/knative/serving (release YAML) |
| Kourier | `knative-v1.15.0` | github.com/knative/net-kourier (release YAML) |
| KServe | `v0.16.0` | `oci://ghcr.io/kserve/charts` |
| kube-prometheus-stack | chart `85.3.3` (app `v0.90.1`) | prometheus-community |
| OpenCost | chart `2.5.21` (app `1.120.2`) | opencost-helm-chart |
| AWS Load Balancer Controller | chart `3.3.0` | aws.github.io/eks-charts |

The KServe-coupled versions (cert-manager, Knative, Kourier, KServe) come from KServe
0.16.0's own `hack/quick_install.sh` — that is the compatibility set KServe validates.
The observability stack (Prometheus, OpenCost) is not version-coupled to KServe, so it
tracks current stable.

## KServe 0.17 upgrade

Pinned to 0.16.x deliberately. The upgrade path is documented in
`helm-values/kserve.yaml`; do it as a separate change (`upgrade-kserve-to-0-17`), not a
mid-flight edit.

## Failure behavior

`bootstrap.sh` stops at the first add-on that does not become Ready within its timeout,
names it, and does not install anything after it. `verify.sh` independently re-checks all
components and exits non-zero naming the first one that is not Ready.
