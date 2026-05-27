# Lab 4 — Canary Rollout & Rollback (15 min)

**Goal:** ship a new model version (v1.0.1) to a slice of traffic, watch the split, promote
it to 100%, and roll back — all by editing one field.

**Prerequisites:** Lab 1's `adult-income-classifier` is deployed and `READY`; `k6` available.

## 1. Start the canary at 10% (3 min)

`lab4-xgboost-canary-v1-0-1.yaml` is the Lab 1 service with the `storageUri` bumped to
v1.0.1 and `canaryTrafficPercent: 10`. Substitute the bucket as in Lab 1, then apply:

```bash
export MODEL_URI="s3://$(terraform -chdir=../cluster/eks/terraform output -raw model_artifacts_bucket_name)/model-v1.0.1"
sed "s#s3://REPLACE_WITH_BUCKET/model-v1.0.1#${MODEL_URI}#" \
  ../manifests/lab4-xgboost-canary-v1-0-1.yaml > /tmp/lab4-canary.yaml
kubectl apply -f /tmp/lab4-canary.yaml -n "$NAMESPACE"

kubectl get revisions -n "$NAMESPACE" \
  -l serving.kserve.io/inferenceservice=adult-income-classifier
```

You now have two revisions: the old (v1.0.0, ~90%) and the new (v1.0.1, ~10%).

## 2. Observe the split (4 min)

```bash
BASE_URL="$BASE_URL" NAMESPACE="$NAMESPACE" DOMAIN="$DOMAIN" \
  k6 run ../tests/load/k6-canary-traffic.js
```

5 RPS for 5 minutes — enough to see the split, not enough to trigger extra autoscaling. The
authoritative split is in Knative:

```bash
kubectl get inferenceservice adult-income-classifier -n "$NAMESPACE" \
  -o jsonpath='{.status.components.predictor.traffic}{"\n"}'
```

You should see ~10% to the latest revision, ~90% to the previous one (8–12% is normal
variance).

## 3. Promote to 100% (2 min)

Remove the split — no `canaryTrafficPercent` means all traffic to the latest revision:

```bash
sed "s#s3://REPLACE_WITH_BUCKET/model-v1.0.1#${MODEL_URI}#" \
  ../manifests/lab4-xgboost-promote.yaml | kubectl apply -n "$NAMESPACE" -f -
```

Re-check the traffic: 100% now goes to v1.0.1, and v1.0.0 remains as the previous good
revision (ready for instant rollback).

## 4. Roll back (3 min)

Suppose the new version misbehaves. `canaryTrafficPercent: 0` sends everything back to the
previous revision — no pod restart, just a traffic shift:

```bash
sed "s#s3://REPLACE_WITH_BUCKET/model-v1.0.1#${MODEL_URI}#" \
  ../manifests/lab4-xgboost-rollback.yaml | kubectl apply -n "$NAMESPACE" -f -
kubectl get inferenceservice adult-income-classifier -n "$NAMESPACE" \
  -o jsonpath='{.status.components.predictor.traffic}{"\n"}'
```

100% returns to v1.0.0, immediately.

## Pass criteria

- Canary step: ~8–12% of traffic on v1.0.1, the rest on v1.0.0.
- Promote step: 100% on v1.0.1, v1.0.0 retained as previous revision.
- Rollback step: 100% back on v1.0.0 with no pod restart.

## What just happened

Progressive delivery for models, declaratively. One field (`canaryTrafficPercent`) drives
canary → promote → rollback, and rollback is instant because the previous revision is still
warm. No blue/green plumbing, no traffic-router config — Knative handles it.
