# nfcu-session-4-tinyllama-predictor-image

## ADDED Requirements

### Requirement: Predictor implements KServe Model interface

`predictors/tinyllama/server.py` SHALL subclass `kserve.Model` and implement `load()` and `predict()`.

#### Scenario: Predictor handles standard KServe requests
- **GIVEN** the container running on port 8080
- **WHEN** a POST hits `/v1/models/tinyllama-completion:predict` with `{"prompt": "...", "max_tokens": 50}`
- **THEN** the response is `{"completion": str, "model": "tinyllama-1.1b", "tokens_generated": N}` where N ≤ 50
- **AND** status is 200

#### Scenario: Readiness gates on weight loading
- **GIVEN** the container just started
- **WHEN** Kubernetes probes readiness
- **THEN** the probe fails until weights are loaded
- **AND** subsequent probes return 200

### Requirement: Image is multi-arch and reproducible

The TinyLlama image SHALL be built for `linux/amd64` and `linux/arm64` from a single Dockerfile via `docker buildx`.

#### Scenario: Build script produces both architectures
- **GIVEN** Docker with buildx and qemu
- **WHEN** the user runs `bash predictors/tinyllama/build.sh`
- **THEN** a multi-arch manifest is produced for both platforms

#### Scenario: Image runs on Apple Silicon without emulation
- **GIVEN** an M-series Mac
- **WHEN** the user runs the image via `docker run`
- **THEN** the container starts in under 30 seconds with no qemu translation

### Requirement: distilGPT-2 fallback exists

`predictors/tinyllama/distilgpt2-fallback.Dockerfile` SHALL produce an interchangeable image using distilGPT-2 weights.

#### Scenario: Fallback is drop-in compatible
- **GIVEN** a lab 3 manifest pointing at the fallback image
- **WHEN** the InferenceService is applied
- **THEN** the same request/response contract holds

### Requirement: Push targets a configurable registry

`predictors/tinyllama/build.sh` SHALL accept a registry override via environment variable.

#### Scenario: Speaker pushes to their own ECR
- **GIVEN** the speaker's AWS account and `REGISTRY=<their-ecr-uri>` env var
- **WHEN** they run `bash push-to-ecr.sh`
- **THEN** the image is built and pushed to the speaker's ECR (created if absent)
- **AND** the resulting URI is printed for use in the lab 3 manifest
