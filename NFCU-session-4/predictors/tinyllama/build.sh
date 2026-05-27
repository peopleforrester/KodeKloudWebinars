#!/usr/bin/env bash
# ABOUTME: Builds the multi-arch (amd64+arm64) TinyLlama predictor image via docker buildx.
# ABOUTME: Registry/tag/Dockerfile are env-overridable; pushes only when PUSH=1.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

REGISTRY="${REGISTRY:-public.ecr.aws/kodekloud-workshop/tinyllama-kserve}"
TAG="${TAG:-0.16.0}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"
DOCKERFILE="${DOCKERFILE:-Dockerfile}"     # set to distilgpt2-fallback.Dockerfile for the fallback
PUSH="${PUSH:-0}"
IMAGE="${REGISTRY}:${TAG}"

require() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: '$1' is required." >&2; exit 2; }; }
require docker
docker buildx version >/dev/null 2>&1 || { echo "ERROR: docker buildx is required for multi-arch builds." >&2; exit 2; }

# A multi-arch manifest can only be exported to a registry, not loaded locally. So a
# multi-platform build implies push. Single-platform builds can be --load'ed for testing.
OUTPUT_FLAG="--push"
if [[ "$PUSH" != "1" ]]; then
  if [[ "$PLATFORMS" == *,* ]]; then
    echo "NOTE: PUSH=0 with multiple platforms — building without exporting (cache only)."
    OUTPUT_FLAG=""
  else
    OUTPUT_FLAG="--load"
  fi
fi

echo "==> Building $IMAGE for [$PLATFORMS] from $DOCKERFILE"
# shellcheck disable=SC2086
docker buildx build \
  --platform "$PLATFORMS" \
  -f "$SCRIPT_DIR/$DOCKERFILE" \
  -t "$IMAGE" \
  $OUTPUT_FLAG \
  "$SCRIPT_DIR"

echo "==> Done: $IMAGE"
[[ "$OUTPUT_FLAG" == "--push" ]] && echo "    Pushed. Use this in lab3-tinyllama-inferenceservice.yaml: image: $IMAGE"
exit 0
