#!/usr/bin/env bash
# ABOUTME: End-to-end rehearsal on local kind — bootstrap, deploy labs 1-4, run k6, teardown.
# ABOUTME: No AWS spend. Target: cold start to teardown in under 30 minutes on a 16 GB laptop.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAMESPACE="${NAMESPACE:-default}"
DOMAIN="${DOMAIN:-example.com}"
BASE_URL="${BASE_URL:-http://localhost:31080}"
PREDICTOR_IMAGE="${PREDICTOR_IMAGE:-tinyllama-kserve:rehearsal}"
SECONDS=0

step() { printf '\n\033[1m### %s (t+%ss) ###\033[0m\n' "$1" "$SECONDS"; }

step "1/7 Bring up kind + add-ons"
bash "$ROOT/cluster/local/up.sh"

step "2/7 Generate model artifacts"
python3 "$ROOT/manifests/model-artifacts/generate-xgboost-models.py"

step "3/7 Build predictor and load it into kind"
DOCKERFILE="${DOCKERFILE:-Dockerfile}" IMAGE="$PREDICTOR_IMAGE" \
  bash "$ROOT/predictors/tinyllama/build.sh" || true   # single-arch --load build
kind load docker-image "$PREDICTOR_IMAGE" --name nfcu-session-4

step "4/7 Stage models onto a PVC (local storageUri path)"
# A model-store PVC + a short-lived pod that the models are copied into.
kubectl apply -n "$NAMESPACE" -f - <<'YAML'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-store
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 1Gi
YAML
kubectl run model-loader -n "$NAMESPACE" --image=busybox --restart=Never \
  --overrides='{"spec":{"containers":[{"name":"model-loader","image":"busybox","command":["sleep","600"],"volumeMounts":[{"name":"m","mountPath":"/mnt/models"}]}],"volumes":[{"name":"m","persistentVolumeClaim":{"claimName":"model-store"}}]}}'
kubectl wait -n "$NAMESPACE" --for=condition=Ready pod/model-loader --timeout=120s
kubectl cp "$ROOT/manifests/model-artifacts/model-v1.0.0" "$NAMESPACE/model-loader:/mnt/models/"
kubectl cp "$ROOT/manifests/model-artifacts/model-v1.0.1" "$NAMESPACE/model-loader:/mnt/models/"
kubectl delete pod model-loader -n "$NAMESPACE" --wait=false

step "5/7 Deploy labs 1-4 (storageUri -> pvc, image -> local)"
deploy() {  # $1 = manifest, $2 = model version
  sed -e "s#s3://REPLACE_WITH_BUCKET/$2#pvc://model-store/$2#" \
      -e "s#public.ecr.aws/kodekloud-workshop/tinyllama-kserve:0.16.0#$PREDICTOR_IMAGE#" \
      "$1" | kubectl apply -n "$NAMESPACE" -f -
}
deploy "$ROOT/manifests/lab1-xgboost-inferenceservice.yaml" model-v1.0.0
kubectl apply -n "$NAMESPACE" -f "$ROOT/manifests/lab2-hpa-baseline-deployment.yaml"
deploy "$ROOT/manifests/lab3-tinyllama-inferenceservice.yaml" model-v1.0.0
kubectl wait -n "$NAMESPACE" --for=condition=Ready inferenceservice --all --timeout=300s

step "6/7 Smoke + load tests"
BASE_URL="$BASE_URL" NAMESPACE="$NAMESPACE" DOMAIN="$DOMAIN" bash "$ROOT/tests/smoke/curl-tests.sh"
BASE_URL="$BASE_URL" NAMESPACE="$NAMESPACE" DOMAIN="$DOMAIN" k6 run "$ROOT/tests/load/k6-xgboost-kserve.js"
BASE_URL="$BASE_URL" NAMESPACE="$NAMESPACE" DOMAIN="$DOMAIN" k6 run "$ROOT/tests/load/k6-tinyllama.js"
# Lab 4 canary
deploy "$ROOT/manifests/lab4-xgboost-canary-v1-0-1.yaml" model-v1.0.1
BASE_URL="$BASE_URL" NAMESPACE="$NAMESPACE" DOMAIN="$DOMAIN" k6 run "$ROOT/tests/load/k6-canary-traffic.js"

step "7/7 Teardown"
bash "$ROOT/cluster/local/down.sh"

printf '\n\033[1mRehearsal complete in %s seconds (%s min).\033[0m\n' "$SECONDS" "$((SECONDS / 60))"
