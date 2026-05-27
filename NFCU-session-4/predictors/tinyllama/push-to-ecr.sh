#!/usr/bin/env bash
# ABOUTME: Pushes the predictor image to a PRIVATE ECR repo in the speaker's AWS account,
# ABOUTME: creating the repo if it does not exist. Then delegates the build to build.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

REGION="${AWS_REGION:-us-east-1}"
REPO="${ECR_REPO:-tinyllama-kserve}"
TAG="${TAG:-0.16.0}"

require() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: '$1' is required." >&2; exit 2; }; }
require aws
require docker

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "==> Ensuring ECR repo '$REPO' exists"
aws ecr describe-repositories --repository-names "$REPO" --region "$REGION" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "$REPO" --region "$REGION" >/dev/null

echo "==> Logging Docker in to $ECR_URI"
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR_URI"

echo "==> Building and pushing"
REGISTRY="${ECR_URI}/${REPO}" TAG="$TAG" PUSH=1 bash "$SCRIPT_DIR/build.sh"

echo
echo "Set this image in manifests/lab3-tinyllama-inferenceservice.yaml:"
echo "  image: ${ECR_URI}/${REPO}:${TAG}"
