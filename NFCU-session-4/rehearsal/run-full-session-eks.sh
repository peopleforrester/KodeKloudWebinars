#!/usr/bin/env bash
# ABOUTME: End-to-end rehearsal on EKS — terraform apply, bootstrap, deploy labs, k6, destroy.
# ABOUTME: Costs real money; always finishes with terraform destroy unless KEEP_CLUSTER=1.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAMESPACE="${NAMESPACE:-default}"
DOMAIN="${DOMAIN:-example.com}"
KEEP_CLUSTER="${KEEP_CLUSTER:-0}"
SECONDS=0

step() { printf '\n\033[1m### %s (t+%ss) ###\033[0m\n' "$1" "$SECONDS"; }

# Always tear down on exit unless explicitly kept — a forgotten EKS cluster is the costly
# mistake this whole runbook guards against.
teardown() {
  if [[ "$KEEP_CLUSTER" == "1" ]]; then
    echo "KEEP_CLUSTER=1 — leaving the cluster up. Remember: bash cluster/eks/down.sh"
  else
    step "Teardown (terraform destroy)"
    yes "$(terraform -chdir="$ROOT/cluster/eks/terraform" output -raw cluster_name 2>/dev/null || echo nfcu-session-4)" \
      | bash "$ROOT/cluster/eks/down.sh" || echo "Destroy reported an issue — verify manually with cluster/eks/down.sh"
  fi
}
trap teardown EXIT

step "1/6 terraform apply"
bash "$ROOT/cluster/eks/up.sh"

step "2/6 Bootstrap add-ons"
bash "$ROOT/cluster/addons/bootstrap.sh" eks
bash "$ROOT/cluster/addons/verify.sh"

step "3/6 Models -> S3, predictor -> ECR"
python3 "$ROOT/manifests/model-artifacts/generate-xgboost-models.py"
bash "$ROOT/manifests/model-artifacts/upload-to-s3.sh"
bash "$ROOT/predictors/tinyllama/push-to-ecr.sh"

step "4/6 Deploy labs 1-4"
BUCKET="$(terraform -chdir="$ROOT/cluster/eks/terraform" output -raw model_artifacts_bucket_name)"
deploy() { sed "s#REPLACE_WITH_BUCKET#$BUCKET#g" "$1" | kubectl apply -n "$NAMESPACE" -f -; }
deploy "$ROOT/manifests/lab1-xgboost-inferenceservice.yaml"
kubectl apply -n "$NAMESPACE" -f "$ROOT/manifests/lab2-hpa-baseline-deployment.yaml"
# Lab 3 image: set REGISTRY/ECR URI in the manifest before applying (push-to-ecr.sh printed it).
kubectl apply -n "$NAMESPACE" -f "$ROOT/manifests/lab3-tinyllama-inferenceservice.yaml" || true
kubectl wait -n "$NAMESPACE" --for=condition=Ready inferenceservice --all --timeout=420s

step "5/6 Smoke + load tests + canary"
BASE_URL="${BASE_URL:?set BASE_URL to the NLB address}" NAMESPACE="$NAMESPACE" DOMAIN="$DOMAIN" \
  bash "$ROOT/tests/smoke/curl-tests.sh"
BASE_URL="$BASE_URL" NAMESPACE="$NAMESPACE" DOMAIN="$DOMAIN" k6 run "$ROOT/tests/load/k6-xgboost-kserve.js"
deploy "$ROOT/manifests/lab4-xgboost-canary-v1-0-1.yaml"
BASE_URL="$BASE_URL" NAMESPACE="$NAMESPACE" DOMAIN="$DOMAIN" k6 run "$ROOT/tests/load/k6-canary-traffic.js"

step "6/6 Done (teardown runs on exit)"
printf '\n\033[1mEKS rehearsal reached the end in %s seconds (%s min).\033[0m\n' "$SECONDS" "$((SECONDS / 60))"
