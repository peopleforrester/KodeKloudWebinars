# Tasks: add-nfcu-session-4-kserve-collateral

Implementation tasks ordered by dependency. Each top-level task ships in roughly one PR's worth of work.
Checkboxes are updated live as the run progresses. See `../../../RUN_CONFIG.md` for path mapping and deviations.

## 1. Repository scaffolding

- [x] 1.1 Create `NFCU-session-4/` at repo root
- [x] 1.2 Create top-level `NFCU-session-4/README.md` with role-based starting points (Platform Engineer / DevOps Engineer / Lab Engineer / Speaker)
- [~] 1.3 Update root `README.md` to add Session 4 — **DEFERRED to maintainer** (scope: do not touch repo root; see RUN_CONFIG)
- [x] 1.4 Create `NFCU-session-4/.gitignore`
- [x] 1.5 Create `NFCU-session-4/Makefile` with targets: `validate`, `bootstrap-local`, `teardown-local`, `eks-up`, `eks-down`, `build-predictor`, `run-rehearsal`, `clean`

## 2. EKS provisioning (nfcu-session-4-eks-cluster)

- [x] 2.1 `cluster/eks/README.md`
- [x] 2.2 `cluster/eks/terraform/versions.tf`
- [x] 2.3 `cluster/eks/terraform/variables.tf`
- [x] 2.4 `cluster/eks/terraform/main.tf`
- [x] 2.5 `cluster/eks/terraform/outputs.tf`
- [x] 2.6 `cluster/eks/terraform/terraform.tfvars.example`
- [x] 2.7 `cluster/eks/up.sh`
- [x] 2.8 `cluster/eks/down.sh`
- [x] 2.9 `terraform validate` passes (against real v20 EKS / v5 IAM / v5 VPC modules)

## 3. Cluster add-ons (nfcu-session-4-cluster-addons)

- [x] 3.1 `cluster/addons/README.md`
- [x] 3.2 `cluster/addons/bootstrap.sh`
- [x] 3.3 `cluster/addons/helm-values/cert-manager.yaml`
- [x] 3.4 `cluster/addons/helm-values/knative-serving.yaml`
- [x] 3.5 `cluster/addons/helm-values/kourier.yaml`
- [x] 3.6 `cluster/addons/helm-values/kserve.yaml`
- [x] 3.7 `cluster/addons/helm-values/kube-prometheus-stack.yaml`
- [x] 3.8 `cluster/addons/helm-values/opencost.yaml`
- [x] 3.9 `cluster/addons/helm-values/aws-load-balancer-controller.yaml`
- [x] 3.10 Version-pinned headers on every helm values file
- [x] 3.11 `cluster/addons/verify.sh`

## 4. Local cluster (nfcu-session-4-local-cluster)

- [x] 4.1 `cluster/local/README.md`
- [x] 4.2 `cluster/local/kind-config.yaml`
- [x] 4.3 `cluster/local/up.sh`
- [x] 4.4 `cluster/local/down.sh`
- [x] 4.5 Min laptop spec documented

## 5. Per-attendee overlays (nfcu-session-4-lab-overlays)

- [ ] 5.1 `cluster/lab-overlays/README.md`
- [ ] 5.2 `cluster/lab-overlays/base/kustomization.yaml`
- [ ] 5.3 `cluster/lab-overlays/base/namespace.yaml`
- [ ] 5.4 `cluster/lab-overlays/base/resourcequota.yaml`
- [ ] 5.5 `cluster/lab-overlays/base/networkpolicy.yaml`
- [ ] 5.6 `cluster/lab-overlays/base/serviceaccount.yaml`
- [ ] 5.7 `cluster/lab-overlays/overlays/attendee-sample/kustomization.yaml`

## 6. Inference service manifests (nfcu-session-4-inferenceservice-manifests)

- [ ] 6.1 `manifests/README.md`
- [ ] 6.2 `manifests/lab1-xgboost-inferenceservice.yaml`
- [ ] 6.3 `manifests/lab2-hpa-baseline-deployment.yaml`
- [ ] 6.4 `manifests/lab3-tinyllama-inferenceservice.yaml`
- [ ] 6.5 `manifests/lab4-xgboost-canary-v1-0-1.yaml`
- [ ] 6.6 `manifests/lab4-xgboost-promote.yaml`
- [ ] 6.7 `manifests/lab4-xgboost-rollback.yaml`
- [ ] 6.8 `manifests/_reference-gpu-vllm.yaml.disabled`
- [ ] 6.9 `manifests/model-artifacts/README.md`
- [ ] 6.10 `manifests/model-artifacts/generate-xgboost-models.py`
- [ ] 6.11 `manifests/model-artifacts/upload-to-s3.sh`
- [ ] 6.12 Active manifests pass `kubectl apply --dry-run=client`

## 7. TinyLlama predictor container (nfcu-session-4-tinyllama-predictor-image)

- [ ] 7.1 `predictors/tinyllama/README.md`
- [ ] 7.2 `predictors/tinyllama/Dockerfile`
- [ ] 7.3 `predictors/tinyllama/pyproject.toml`
- [ ] 7.4 `predictors/tinyllama/server.py`
- [ ] 7.5 `predictors/tinyllama/health.py`
- [ ] 7.6 `predictors/tinyllama/distilgpt2-fallback.Dockerfile`
- [ ] 7.7 `predictors/tinyllama/build.sh`
- [ ] 7.8 `predictors/tinyllama/push-to-ecr.sh`
- [ ] 7.9 `predictors/tinyllama/test-local.sh`
- [ ] 7.10 `predictors/tinyllama/.dockerignore`

## 8. Load test harness (nfcu-session-4-load-test-harness)

- [ ] 8.1 `tests/README.md`
- [ ] 8.2 `tests/smoke/sample-payload-xgboost.json`
- [ ] 8.3 `tests/smoke/sample-payload-llm.json`
- [ ] 8.4 `tests/smoke/curl-tests.sh`
- [ ] 8.5 `tests/load/k6-xgboost-kserve.js`
- [ ] 8.6 `tests/load/k6-xgboost-hpa.js`
- [ ] 8.7 `tests/load/k6-tinyllama.js`
- [ ] 8.8 `tests/load/k6-canary-traffic.js`
- [ ] 8.9 `tests/load/compare-scaling.sh`

## 9. Attendee collateral (nfcu-session-4-collateral)

- [ ] 9.1 `attendee-guide/README.md`
- [ ] 9.2 `attendee-guide/prerequisites.md`
- [ ] 9.3 `attendee-guide/lab-1-deploy-inferenceservice.md`
- [ ] 9.4 `attendee-guide/lab-2-load-test-and-scaling.md`
- [ ] 9.5 `attendee-guide/lab-3-llm-and-costs.md`
- [ ] 9.6 `attendee-guide/lab-4-canary-rollout.md`
- [ ] 9.7 `attendee-guide/reproduce-on-your-aws-account.md`
- [ ] 9.8 `attendee-guide/post-session-monday-actions.md`
- [ ] 9.9 `attendee-guide/faq.md`
- [ ] 9.10 `reference-card/kserve-on-k8s.md`

## 10. Operations runbook (nfcu-session-4-operations-runbook)

- [ ] 10.1 `runbook/README.md`
- [ ] 10.2 `runbook/definition-of-done.md`
- [ ] 10.3 `runbook/troubleshooting-matrix.md`
- [ ] 10.4 `runbook/day-of-operations.md`
- [ ] 10.5 `runbook/cleanup-automation.md`
- [ ] 10.6 `runbook/dry-run-checklist.md`
- [ ] 10.7 `runbook/speaker-aws-spend.md`

## 11. Speaker rehearsal path

- [ ] 11.1 `rehearsal/README.md`
- [ ] 11.2 `rehearsal/run-full-session-local.sh`
- [ ] 11.3 `rehearsal/run-full-session-eks.sh`
- [ ] 11.4 `rehearsal/timing-notes.md`

## 12. CI

- [ ] 12.1 Folder-local workflow / Makefile `validate` (root `.github/` not created — see RUN_CONFIG)
- [ ] 12.2 Makefile `validate` target runs the checks locally

## 13. Archive

- [ ] 13.1 Move `specs/*` to `openspec/specs/*`
- [ ] 13.2 Delete the change directory after archival
