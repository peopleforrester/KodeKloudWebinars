# nfcu-session-4-inferenceservice-manifests

## ADDED Requirements

### Requirement: Lab 1 manifest deploys XGBoost via KServe

`manifests/lab1-xgboost-inferenceservice.yaml` SHALL deploy XGBoost v1.0.0 in Knative deployment mode with `minReplicas: 0`, `maxReplicas: 5`, `containerConcurrency: 50`.

#### Scenario: Manifest applies cleanly
- **GIVEN** a cluster with KServe 0.16+ and the v1.0.0 model artifact accessible
- **WHEN** the user runs `kubectl apply -f manifests/lab1-xgboost-inferenceservice.yaml -n <namespace>`
- **THEN** within 90 seconds the InferenceService is READY
- **AND** a prediction request returns the expected schema

#### Scenario: Scale-to-zero works after idle
- **GIVEN** a deployed Lab 1 InferenceService with no traffic
- **WHEN** 60 seconds pass with no requests
- **THEN** the predictor pod count drops to 0

### Requirement: Lab 2 HPA baseline demonstrates the anti-pattern

`manifests/lab2-hpa-baseline-deployment.yaml` SHALL deploy the same XGBoost model as a plain Deployment with a CPU-based HPA, used as the "wrong way" comparison in Lab 2.

#### Scenario: HPA scales on CPU, not concurrency
- **GIVEN** the HPA baseline under k6 load
- **WHEN** request volume rises faster than CPU
- **THEN** HPA does not scale up until CPU crosses its threshold
- **AND** the lag is observable and contrasts with the KServe behavior

### Requirement: Lab 3 deploys TinyLlama on CPU

`manifests/lab3-tinyllama-inferenceservice.yaml` SHALL deploy the custom TinyLlama predictor with `minReplicas: 0`, `maxReplicas: 3`, `containerConcurrency: 5`, memory `requests: 4Gi / limits: 6Gi`, no GPU resources requested.

#### Scenario: LLM endpoint comes up
- **GIVEN** a cluster with the TinyLlama image pre-pulled
- **WHEN** the lab 3 manifest is applied
- **THEN** within 120 seconds the InferenceService is READY
- **AND** a completion request returns a non-empty `completion` field

### Requirement: Lab 4 canary uses canaryTrafficPercent

`manifests/lab4-xgboost-canary-v1-0-1.yaml` SHALL update the same `adult-income-classifier` InferenceService's storageUri to v1.0.1 and add `canaryTrafficPercent: 10`.

#### Scenario: Traffic split is observable
- **GIVEN** Lab 1's InferenceService is running v1.0.0
- **WHEN** the canary manifest is applied
- **THEN** ~10% of requests go to v1.0.1 and ~90% to v1.0.0

#### Scenario: Promotion via field removal
- **GIVEN** a canary at 10% to v1.0.1
- **WHEN** `lab4-xgboost-promote.yaml` (no canaryTrafficPercent) is applied
- **THEN** 100% of traffic goes to v1.0.1
- **AND** v1.0.0 remains as previous good revision

#### Scenario: Rollback pins to previous revision
- **GIVEN** a canary at any percentage to v1.0.1
- **WHEN** `lab4-xgboost-rollback.yaml` (canaryTrafficPercent: 0) is applied
- **THEN** 100% of traffic returns to v1.0.0
- **AND** no pod restart occurs

### Requirement: GPU reference YAML is non-applicable

`_reference-gpu-vllm.yaml.disabled` SHALL contain a complete GPU + vLLM reference manifest but SHALL NOT be applicable via `kubectl apply -f manifests/`.

#### Scenario: Bulk apply skips the reference file
- **GIVEN** the manifests directory
- **WHEN** `kubectl apply -f manifests/` runs
- **THEN** the `.disabled` file is ignored
- **AND** no GPU resources are requested

### Requirement: Model artifacts are generated, not committed

`manifests/model-artifacts/generate-xgboost-models.py` SHALL produce both v1.0.0 and v1.0.1 deterministically from UCI Adult Census Income.

#### Scenario: Models are reproducible
- **GIVEN** Python 3.12+ with xgboost, pandas, scikit-learn
- **WHEN** the user runs the generation script
- **THEN** `model-v1.0.0/model.bst` and `model-v1.0.1/model.bst` are produced
- **AND** the same seed produces byte-identical files

#### Scenario: Models upload to S3 from Terraform output
- **GIVEN** the EKS cluster is provisioned
- **WHEN** the user runs `bash manifests/model-artifacts/upload-to-s3.sh`
- **THEN** the script reads the bucket name from `terraform output`
- **AND** both models are uploaded to the expected keys
