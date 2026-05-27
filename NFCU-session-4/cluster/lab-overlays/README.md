# Per-Attendee Namespace Overlays

kustomize base + a sample overlay for the isolated namespace each attendee works in. **The
KodeKloud lab platform owns per-attendee provisioning** — it consumes these overlays to
stamp ~30 namespaces. We ship the base and one worked example; we do not provision the 30.

## What the base produces

`kubectl kustomize base` renders, for one attendee:

| Resource | Purpose |
|---|---|
| `Namespace` | The attendee's isolated workspace |
| `ResourceQuota` | Caps the namespace at **4 vCPU / 8 Gi / 10 pods** so no one starves the cluster |
| `NetworkPolicy` | Blocks traffic from *other attendee* namespaces (see the nuance below) |
| `ServiceAccount` (`kserve-sa`) | Runs the KServe storage initializer; bound to the S3-reader role via an EKS Pod Identity association |

## Stamping per attendee

The only per-attendee difference is the namespace name. The sample overlay shows the
pattern:

```bash
# Render the sample
kubectl kustomize overlays/attendee-sample | kubectl apply -f -

# Mass-produce (what the lab platform does) — loop the namespace value:
for i in $(seq -w 1 30); do
  kubectl kustomize base \
    | sed "s/namespace: attendee/namespace: attendee-$i/" \
    | kubectl apply -f -
done
```

Setting kustomize's `namespace:` both renames the `Namespace` object and stamps the
namespace onto the quota, network policy, and service account — so one line is the entire
per-attendee diff.

## NetworkPolicy nuance (important)

A literal "deny all cross-namespace" policy **breaks the lab**: Kourier and the Knative
activator live in their own namespaces and must reach the predictor pods to route requests
and scale from zero. So `base/networkpolicy.yaml` denies traffic from *other attendee*
namespaces but explicitly allows `knative-serving`, `kourier-system`, `kube-system`, and
`monitoring`. Attendee A still cannot reach attendee B — which is the isolation the session
demonstrates.

## Pod Identity (storage initializer auth on EKS)

`base/serviceaccount.yaml` is a plain `kserve-sa` ServiceAccount — **no annotation**. On
EKS, auth is EKS Pod Identity, which binds outside the manifest. Because Pod Identity
associations are per (namespace, service account) with no wildcard, the lab platform creates
one association per attendee namespace when it stamps the namespace:

```bash
aws eks create-pod-identity-association --cluster-name <cluster> \
  --namespace attendee-0001 --service-account kserve-sa \
  --role-arn "$(terraform -chdir=../eks/terraform output -raw kserve_s3_role_arn)"
```

On local kind there is no Pod Identity; the SA is just a plain SA and models load from a PVC.
