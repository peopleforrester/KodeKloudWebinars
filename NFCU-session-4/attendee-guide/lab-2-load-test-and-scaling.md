# Lab 2 — Load Test & Autoscaling (12 min)

**Goal:** see KServe scale on *concurrency* and contrast it with a plain CPU-based HPA doing
the same job the "normal" way. The gap is the point of the lab.

**Prerequisites:** Lab 1 deployed; `k6` available; `$BASE_URL`, `$NAMESPACE`, `$DOMAIN` set.

## 1. Deploy the HPA baseline (2 min)

The same XGBoost model, but as a plain Deployment + Service + CPU HorizontalPodAutoscaler —
the way you'd do it without KServe.

```bash
kubectl apply -f ../manifests/lab2-hpa-baseline-deployment.yaml -n "$NAMESPACE"
kubectl get hpa xgboost-hpa-baseline -n "$NAMESPACE"
```

## 2. Load test the KServe service (4 min)

```bash
BASE_URL="$BASE_URL" NAMESPACE="$NAMESPACE" DOMAIN="$DOMAIN" \
  k6 run ../tests/load/k6-xgboost-kserve.js
```

In another terminal, watch pods scale out during the 3-minute hold:

```bash
kubectl get pods -n "$NAMESPACE" \
  -l serving.kserve.io/inferenceservice=adult-income-classifier -w
```

KServe adds pods as in-flight requests cross `containerConcurrency: 50` — it reacts to load
directly, not to a lagging CPU signal.

## 3. Load test the HPA baseline (4 min)

```bash
# port-forward the ClusterIP service, then run the same ramp
kubectl -n "$NAMESPACE" port-forward svc/xgboost-hpa-baseline 8081:80 &
BASE_URL=http://localhost:8081 k6 run ../tests/load/k6-xgboost-hpa.js
kill %1   # stop the port-forward
```

Watch the HPA: it won't add pods until average CPU crosses 50%, which lags the actual
request surge. You'll see higher tail latency during ramp-up.

## 4. Compare them side by side (2 min)

```bash
NAMESPACE="$NAMESPACE" bash ../tests/load/compare-scaling.sh
```

This runs both ramps while sampling pod counts and prints, for each:
time-to-scale-up, peak pod count, and time-to-scale-down.

## Pass criteria

- The KServe service scales above 1 pod during the hold and back toward 0 afterward.
- The HPA baseline scales later (on CPU) and floors at 1 pod (never to zero).
- `compare-scaling.sh` prints a row for each with a visibly earlier scale-up for KServe.

## What just happened

Concurrency-based autoscaling reacts to the thing you actually care about — requests in
flight — and scales to zero when idle. CPU-based HPA is a proxy that lags and can't reach
zero. Same model, very different operational behavior.
