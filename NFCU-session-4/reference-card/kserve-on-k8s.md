# KServe on Kubernetes — Reference Card

*NFCU Session 4. One page. Print at 0.5" margins.*

## Core primitives

| Primitive | What it is |
|---|---|
| `InferenceService` | The unit you deploy: a model + its serving config + autoscaling + traffic. |
| Predictor | Serves the model. Either `model:` (built-in runtime by `modelFormat`) or `containers:` (custom, e.g. the LLM). |
| Transformer | Optional pre/post-processing step in front of the predictor. |
| Storage initializer | Init container that pulls the artifact from `storageUri` (s3/gs/pvc/http). |
| Revision | An immutable snapshot of a predictor version. Traffic splits across revisions. |

## Minimal InferenceService

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata: { name: my-model }
spec:
  predictor:
    minReplicas: 0          # scale-to-zero
    maxReplicas: 5
    containerConcurrency: 50 # scale on in-flight requests
    model:
      modelFormat: { name: xgboost }
      storageUri: s3://bucket/model-v1
```

## Deployment modes

| | Knative (this session) | Standard |
|---|---|---|
| Scale-to-zero | ✅ | ❌ |
| Concurrency autoscaling | ✅ | ❌ (HPA on CPU/mem only) |
| `canaryTrafficPercent` | ✅ | ❌ |
| Needs | Knative + ingress (Kourier) | Just Deployments |

Use Knative when you want serverless behavior and progressive delivery — which is most model
serving. Standard only when you can't run Knative.

## Autoscaling knobs

- `containerConcurrency` — target in-flight requests per pod (the main lever).
- `minReplicas: 0` — scale to zero when idle (cold start on next request).
- `minReplicas: 1` — keep one warm (latency-sensitive, always-on).
- `maxReplicas` — ceiling. Pods × concurrency = peak capacity.

## GPU cost levers (production)

- Request `nvidia.com/gpu` only on the predictor that needs it; keep the rest CPU.
- Use the HF/vLLM runtime on GPU for LLMs (much higher throughput than CPU transformers).
- `minReplicas: 0` on GPU models is the biggest saver — idle GPUs are the expensive ones.
- Right-size: a 1.1B model needs ~4–6 Gi on CPU; large LLMs need GPU memory, not just count.
- Attribute cost per model (OpenCost) so the expensive model is obvious, not a guess.

## Canary vs shadow

| | Canary (`canaryTrafficPercent: N`) | Shadow (mirror) |
|---|---|---|
| Traffic | N% of *real* users hit the new version | New version gets a *copy*; users unaffected |
| Sees real responses | Yes (users do) | No (responses discarded) |
| Risk to users | Some (N%) | None |
| Use when | You'll promote if metrics look good | You want to test load/behavior with zero user risk |

Promote: remove `canaryTrafficPercent` → 100% new. Rollback: `canaryTrafficPercent: 0` →
100% previous revision, instantly, no restart.

## Request shape (v1)

```bash
curl -X POST $INGRESS/v1/models/<name>:predict \
  -H "Host: <name>.<ns>.<domain>" \
  -d '{"instances": [[...]]}'        # or {"prompt": "...", "max_tokens": 50} for the LLM
```

## When it breaks

503 on first request → cold start, retry · stuck `READY=False` → storage initializer
(check `storageUri` + Pod Identity) · pod Pending → quota/resources · no split → still one revision.
