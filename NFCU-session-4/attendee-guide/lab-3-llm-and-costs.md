# Lab 3 — An LLM and Its Cost (15 min)

**Goal:** put a small LLM (TinyLlama 1.1B, CPU) behind the same `InferenceService` API, then
attribute its cost per model with OpenCost.

**Prerequisites:** the TinyLlama image is pushed (your lab engineer did this) and its tag is
set in the manifest; `$BASE_URL`, `$NAMESPACE`, `$DOMAIN` set.

## 1. Deploy TinyLlama (3 min)

```bash
kubectl apply -f ../manifests/lab3-tinyllama-inferenceservice.yaml -n "$NAMESPACE"
kubectl get inferenceservice tinyllama-completion -n "$NAMESPACE" -w
```

LLM cold-start is slower than XGBoost — weights load into memory. Expect `READY=True`
within ~120s. (If Hugging Face was rate-limited on build day, your engineer swapped in the
distilGPT-2 fallback image — same API, weaker text.)

## 2. Generate a completion (2 min)

```bash
curl -s -X POST \
  "${BASE_URL}/v1/models/tinyllama-completion:predict" \
  -H 'Content-Type: application/json' \
  -H "Host: tinyllama-completion.${NAMESPACE}.${DOMAIN}" \
  -d @../tests/smoke/sample-payload-llm.json
```

Expected shape:

```json
{ "completion": "…generated text…", "model": "tinyllama-1.1b", "tokens_generated": 50 }
```

## 3. Put some load on it (3 min)

```bash
BASE_URL="$BASE_URL" NAMESPACE="$NAMESPACE" DOMAIN="$DOMAIN" \
  k6 run ../tests/load/k6-tinyllama.js
```

The gentle 1→10 VU ramp stays within `containerConcurrency: 5 × maxReplicas: 3`, so error
rate stays under 1% while you generate enough usage for the cost view to populate.

## 4. See the cost per model (5 min)

OpenCost prices each workload by its resource usage. Open the UI:

```bash
kubectl -n opencost port-forward svc/opencost 9090:9090 &
# open http://localhost:9090  (or the OpenCost Grafana dashboard)
```

Compare your two models in your namespace:

- **`adult-income-classifier`** (XGBoost): tiny CPU/memory → fractions of a cent/hour.
- **`tinyllama-completion`** (LLM): 1–2 vCPU and 4–6 Gi → noticeably more per hour, and it
  only earns that cost while serving (scale-to-zero when idle).

This is the cost-attribution point: same platform, same API, but the LLM's footprint — and
bill — is an order of magnitude larger. Per-attendee target for the whole session is ≤ $1.60.

## Pass criteria

- `tinyllama-completion` reports `READY=True` and returns a non-empty `completion`.
- The k6 LLM run keeps error rate under 1%.
- OpenCost shows distinct, plausible per-model costs for the two services.

## What just happened

The LLM uses the exact same `InferenceService` contract as the XGBoost model — different
runtime, identical operations. And because cost is attributed per workload, "which model is
expensive?" stops being a guess.
