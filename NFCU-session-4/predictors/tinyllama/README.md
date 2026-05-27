# TinyLlama Predictor (Custom KServe Runtime)

A small KServe predictor that serves **TinyLlama 1.1B on CPU** via Hugging Face
`transformers`. Custom rather than KServe's built-in Hugging Face runtime because that
runtime defaults to vLLM (GPU-only); a custom predictor gives us a tiny CPU image and an
input/output schema that matches the attendee-guide curl examples exactly.

Multi-arch (`linux/amd64`, `linux/arm64`) so it runs natively on Apple Silicon laptops and
on EKS nodes without emulation. Weights are baked in at build time, so the container is
**fully offline at runtime** — session day never depends on Hugging Face being reachable.

## API

`POST /v1/models/tinyllama-completion:predict`

```json
{ "prompt": "The future of cloud-native ML is", "max_tokens": 50 }
```

```json
{ "completion": "…generated text…", "model": "tinyllama-1.1b", "tokens_generated": 50 }
```

Readiness (`GET /v1/models/tinyllama-completion`) returns 200 only after the weights finish
loading — `server.py` loads in `__init__`, so the HTTP server comes up ready.

## Files

| File | Purpose |
|---|---|
| `server.py` | `kserve.Model` subclass: `load()` reads baked weights, `predict()` generates greedy completions |
| `health.py` | Liveness/readiness probe helper (stdlib only); usable as httpGet or exec |
| `Dockerfile` | Multi-stage, multi-arch CPU image; bakes TinyLlama weights |
| `distilgpt2-fallback.Dockerfile` | Drop-in fallback using distilGPT-2 (same schema, ~350 MB) |
| `pyproject.toml` | Pinned deps (kserve 0.16, transformers 4.50, torch 2.5 CPU, fastapi 0.115) |
| `build.sh` | `docker buildx` multi-arch build; registry/tag via env |
| `push-to-ecr.sh` | Build + push to a private ECR repo in your account (creates it if absent) |
| `test-local.sh` | Build, run, send one request, assert non-empty completion |
| `.dockerignore` | Keeps the build context to just the code + deps |

## Build and publish

```bash
# Multi-arch build to the default public registry (requires push permission):
PUSH=1 bash build.sh

# Or to your own ECR (auto-creates the repo, logs in, builds, pushes):
AWS_REGION=us-east-1 bash push-to-ecr.sh

# Override the target registry/tag:
REGISTRY=myrepo/tinyllama TAG=0.16.0 PUSH=1 bash build.sh

# Build the distilGPT-2 fallback instead:
DOCKERFILE=distilgpt2-fallback.Dockerfile PUSH=1 bash build.sh
```

## torch CPU build

`torch==2.5.*` defaults to the CUDA build on PyPI. The Dockerfile passes
`--extra-index-url https://download.pytorch.org/whl/cpu` so the CPU wheel is selected —
smaller image, no GPU drivers. If you install locally for development, do the same:

```bash
pip install --extra-index-url https://download.pytorch.org/whl/cpu \
    "torch==2.5.*" "transformers==4.50.*" "kserve==0.16.*" "fastapi==0.115.*"
```

## Test locally

```bash
bash test-local.sh    # builds host-arch image, runs it, asserts a non-empty completion
```

On <16 GB laptops, use the fallback: `DOCKERFILE=distilgpt2-fallback.Dockerfile bash test-local.sh`.
