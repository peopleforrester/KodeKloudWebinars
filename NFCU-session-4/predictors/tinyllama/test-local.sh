#!/usr/bin/env bash
# ABOUTME: Smoke-tests the predictor image locally — runs it, sends one completion request,
# ABOUTME: asserts the completion is non-empty, then cleans up. Single-arch (host) build.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${IMAGE:-tinyllama-kserve:test}"
DOCKERFILE="${DOCKERFILE:-Dockerfile}"
CONTAINER="tinyllama-test-$$"
PORT="${PORT:-8080}"
MODEL_NAME="tinyllama-completion"

require() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: '$1' is required." >&2; exit 2; }; }
require docker
require curl

cleanup() { docker rm -f "$CONTAINER" >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "==> Building $IMAGE (host arch) from $DOCKERFILE"
docker build -f "$SCRIPT_DIR/$DOCKERFILE" -t "$IMAGE" "$SCRIPT_DIR"

echo "==> Starting container"
docker run -d --name "$CONTAINER" -p "${PORT}:8080" "$IMAGE" >/dev/null

echo "==> Waiting for readiness (model load can take a minute on CPU)"
ready=""
for _ in $(seq 1 60); do
  if curl -fsS "http://localhost:${PORT}/v1/models/${MODEL_NAME}" >/dev/null 2>&1; then
    ready=1; break
  fi
  sleep 5
done
[[ -z "$ready" ]] && { echo "FAIL: model never became ready"; docker logs "$CONTAINER" | tail -30; exit 1; }

echo "==> Sending a completion request"
RESPONSE="$(curl -fsS -X POST \
  "http://localhost:${PORT}/v1/models/${MODEL_NAME}:predict" \
  -H 'Content-Type: application/json' \
  -d @"$SCRIPT_DIR/../../tests/smoke/sample-payload-llm.json")"
echo "    response: $RESPONSE"

COMPLETION="$(printf '%s' "$RESPONSE" | jq -r '.completion // empty' 2>/dev/null || true)"
if [[ -z "$COMPLETION" ]]; then
  echo "FAIL: empty or missing 'completion' in response"
  exit 1
fi

echo "PASS: got a non-empty completion."
