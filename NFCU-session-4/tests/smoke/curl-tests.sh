#!/usr/bin/env bash
# ABOUTME: Sends one prediction to each endpoint before any load test. Fast fail: each must
# ABOUTME: return 200 within 5s or the script exits non-zero naming the failed endpoint.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Cluster-specific: the Kourier ingress and the Knative host for each service.
BASE_URL="${BASE_URL:-http://localhost:31080}"
NAMESPACE="${NAMESPACE:-default}"
DOMAIN="${KNATIVE_DOMAIN:-example.com}"

XGB_SVC="adult-income-classifier"
LLM_SVC="tinyllama-completion"

fail() { echo "FAIL: endpoint '$1' did not return 200 (got '$2')." >&2; exit 1; }

probe() {
  local svc="$1" payload="$2"
  local host="${svc}.${NAMESPACE}.${DOMAIN}"
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 \
    -X POST "${BASE_URL}/v1/models/${svc}:predict" \
    -H 'Content-Type: application/json' \
    -H "Host: ${host}" \
    -d @"$payload")" || code="000"
  [[ "$code" == "200" ]] || fail "$svc" "$code"
  echo "  ok: $svc -> 200"
}

echo "==> Smoke-testing endpoints at $BASE_URL (namespace=$NAMESPACE)"
probe "$XGB_SVC" "$SCRIPT_DIR/sample-payload-xgboost.json"
probe "$LLM_SVC" "$SCRIPT_DIR/sample-payload-llm.json"
echo "All endpoints healthy."
