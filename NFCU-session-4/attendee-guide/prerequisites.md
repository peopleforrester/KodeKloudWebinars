# Prerequisites

You work in a pre-provisioned namespace on a shared cluster (the lab platform sets this
up). You need only a browser terminal and the basics below. If you're reproducing later on
your own cluster, see [`reproduce-on-your-aws-account.md`](reproduce-on-your-aws-account.md).

## What the lab platform gives you

- A namespace with a `ResourceQuota` (4 vCPU / 8 Gi / 10 pods) and a `kserve-sa`
  ServiceAccount already wired for model storage.
- `kubectl` pre-authenticated to that namespace.
- The cluster already has KServe, Knative, Kourier, Prometheus/Grafana, and OpenCost
  installed.

## Check your access (1 minute)

```bash
kubectl config current-context
kubectl get serviceaccount kserve-sa          # should exist in your namespace
kubectl auth can-i create inferenceservice    # should print "yes"
```

## Know your two endpoints

Every request goes through the Kourier ingress with a `Host` header that routes to your
service:

```bash
export BASE_URL=http://localhost:31080         # lab platform tells you the real value
export NAMESPACE=$(kubectl config view --minify -o jsonpath='{..namespace}')
export DOMAIN=example.com                       # lab platform tells you the real value
```

You'll reuse `$BASE_URL`, `$NAMESPACE`, and `$DOMAIN` in every lab.

## Conventions in these docs

- Every command block is copy-paste runnable once the three variables above are set.
- "Expected output" shows the shape, not the exact bytes — pod names and timestamps vary.
- Each lab states its **pass criteria** at the end. If you hit them, move on.

## If you're on the local (kind) path

Bring the cluster up first (see [`../cluster/local/`](../cluster/local/README.md)):

```bash
bash ../cluster/local/up.sh
```

Then `BASE_URL=http://localhost:31080` and `NAMESPACE=default` work out of the box.
