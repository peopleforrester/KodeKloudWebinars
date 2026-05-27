# FAQ

The questions that come up every time.

## Why KServe instead of just a Deployment + Service?

You can serve a model with a plain Deployment (that's Lab 2's baseline). KServe adds the
things you'd otherwise build by hand: a storage initializer that pulls model artifacts,
concurrency-based autoscaling, scale-to-zero, and `canaryTrafficPercent` traffic splitting.
Lab 2 makes the autoscaling difference concrete.

## Why Knative deployment mode and not Standard?

Knative mode is what gives you scale-to-zero, concurrency autoscaling, and
`canaryTrafficPercent`. KServe's Standard mode loses all three. The whole session depends on
them, so the cluster runs Knative mode.

## Why Kourier and not Istio?

Kourier is the simplest Knative network layer — no service mesh to learn or operate. Istio
adds ~30 minutes to cluster bootstrap and a lot of surface area that's irrelevant to the
session. On EKS, Kourier sits behind an NLB.

## What about Gateway API?

It's the direction Knative networking is heading and worth tracking, but it's not in this
lab — Kourier keeps the moving parts minimal. Nothing here blocks a later move to Gateway
API; it's a network-layer swap.

## Why TinyLlama and not a "real" LLM?

The lab cluster is CPU-only. TinyLlama 1.1B runs on CPU in 4–6 Gi and produces output good
enough for the cost-attribution exercise. The point of Lab 3 isn't the model's quality — it's
that an LLM uses the *same* `InferenceService` API and costs an order of magnitude more to
serve. distilGPT-2 is the fallback if Hugging Face throttles downloads.

## Why a custom predictor instead of KServe's Hugging Face runtime?

KServe's built-in Hugging Face runtime defaults to vLLM, which is GPU-only. A custom CPU
predictor (≈150 lines of Python) gives a small image and an input/output schema that matches
these curl examples exactly.

## Can I use a GPU?

Yes, in production. `manifests/_reference-gpu-vllm.yaml.disabled` shows the GPU + vLLM shape.
It's intentionally not applied here (the lab cluster has no GPUs); rename it to `.yaml` only
on a GPU cluster.

## Does scale-to-zero hurt latency?

The first request after idle pays a cold start (the pod has to come back). For spiky or
dev/test traffic that's a great trade — you pay nothing while idle. For latency-sensitive,
always-on services, set `minReplicas: 1` and keep one pod warm. It's a per-service choice.

## How is per-model cost computed?

OpenCost prices each workload from its actual CPU/memory usage and the node prices. Because
each model is its own workload, you get cost per model rather than one cluster bill. Lab 3
walks through it.

## What does this cost to run myself?

Local kind: nothing (your laptop). Your own EKS: $40–$70 for an 8-hour window — see
[`reproduce-on-your-aws-account.md`](reproduce-on-your-aws-account.md). Always tear the EKS
cluster down when finished.

## The model won't load, or I get a 503 on the first request

That's almost always a cold start (scale-to-zero) or the storage initializer still pulling
the artifact. Wait and retry. If it persists, your lab engineer has the
[troubleshooting matrix](../runbook/troubleshooting-matrix.md) — common causes are a wrong
`storageUri` or missing IRSA permissions on the bucket.
