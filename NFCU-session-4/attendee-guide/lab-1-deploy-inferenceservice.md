# Lab 1 — Deploy an XGBoost InferenceService (12 min)

**Goal:** deploy a trained XGBoost model as a KServe `InferenceService`, make a prediction,
and watch it scale to zero when idle.

**Prerequisites:** `prerequisites.md` done; `$BASE_URL`, `$NAMESPACE`, `$DOMAIN` set.

## 1. Set the model location (1 min)

The manifest ships with a placeholder `storageUri`. Substitute the real one:

```bash
# EKS: the bucket from terraform output; Local: pvc://model-store/model-v1.0.0
export MODEL_URI="s3://$(terraform -chdir=../cluster/eks/terraform output -raw model_artifacts_bucket_name)/model-v1.0.0"
sed "s#s3://REPLACE_WITH_BUCKET/model-v1.0.0#${MODEL_URI}#" \
  ../manifests/lab1-xgboost-inferenceservice.yaml > /tmp/lab1.yaml
```

## 2. Deploy (2 min)

```bash
kubectl apply -f /tmp/lab1.yaml -n "$NAMESPACE"
kubectl get inferenceservice adult-income-classifier -n "$NAMESPACE" -w
```

Expected (within ~90s):

```
NAME                       URL                                          READY
adult-income-classifier    http://adult-income-classifier.<ns>....      True
```

Press Ctrl-C when `READY` is `True`.

## 3. Make a prediction (2 min)

```bash
curl -s -X POST \
  "${BASE_URL}/v1/models/adult-income-classifier:predict" \
  -H 'Content-Type: application/json' \
  -H "Host: adult-income-classifier.${NAMESPACE}.${DOMAIN}" \
  -d @../tests/smoke/sample-payload-xgboost.json
```

Expected shape:

```json
{ "predictions": [0] }
```

(`0` = income ≤ $50K, `1` = > $50K for the sample row.)

## 4. Watch it scale to zero (5 min)

With no traffic, KServe scales the predictor to zero — you pay nothing for an idle model.

```bash
kubectl get pods -n "$NAMESPACE" -l serving.kserve.io/inferenceservice=adult-income-classifier -w
```

After ~60 seconds of no requests the pod count drops to 0. Send another prediction (step 3)
and watch a pod cold-start back up (the first request after scale-to-zero is slower — that's
the cold start you'll load-test in Lab 2).

## Pass criteria

- `InferenceService` reports `READY=True`.
- A prediction returns `{"predictions": [...]}` with HTTP 200.
- The predictor pod scales to 0 after ~60s idle and back to 1 on the next request.

## What just happened

You declared a model, not a deployment. KServe pulled the artifact (via the storage
initializer using the `kserve-sa` IRSA role on EKS), wrapped it in a server, put it behind
Knative, and gave it a URL — with scale-to-zero for free. Lab 2 shows how it scales *up*.
