#!/usr/bin/env bash
# ABOUTME: Verifies the cosign signature on a model image before any Terraform action;
# ABOUTME: a failed verification blocks the deploy.
set -euo pipefail

# --- Required configuration (from environment / CI) -------------------------
: "${ECR_REGISTRY:?ECR_REGISTRY is required (e.g. <account>.dkr.ecr.us-east-1.amazonaws.com)}"
: "${IMAGE_REPO:?IMAGE_REPO is required (ECR repository name)}"
: "${KMS_KEY_ID:?KMS_KEY_ID is required (KMS key id/alias/arn used to sign)}"
: "${IMAGE_DIGEST:?IMAGE_DIGEST is required (sha256:... from the build job)}"

IMAGE_BY_DIGEST="${ECR_REGISTRY}/${IMAGE_REPO}@${IMAGE_DIGEST}"

log() { printf '==> %s\n' "$*"; }

main() {
  log "Verifying signature on ${IMAGE_BY_DIGEST}"
  # Verify by digest (immutable). Non-zero exit here gates terraform plan/apply,
  # so an unsigned or tampered image stops the deploy before any AWS change.
  if ! cosign verify --key "awskms://${KMS_KEY_ID}" "${IMAGE_BY_DIGEST}"; then
    echo "FATAL: signature verification failed for ${IMAGE_BY_DIGEST}" >&2
    exit 1
  fi
  log "Signature verified"
}

main "$@"
