#!/usr/bin/env bash
# ABOUTME: Builds, scans, signs, and pushes the model serving image, emitting the
# ABOUTME: pushed image digest for downstream deploy jobs to consume.
set -euo pipefail

# --- Required configuration (from environment / CI) -------------------------
: "${ECR_REGISTRY:?ECR_REGISTRY is required (e.g. <account>.dkr.ecr.us-east-1.amazonaws.com)}"
: "${IMAGE_REPO:?IMAGE_REPO is required (ECR repository name)}"
: "${KMS_KEY_ID:?KMS_KEY_ID is required (KMS key id/alias/arn for cosign signing)}"
IMAGE_TAG="${IMAGE_TAG:-v1.0.0}"
MODEL_ARTIFACT="${MODEL_ARTIFACT:-model-v1.0.0.tar.gz}"
BUILD_CONTEXT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

IMAGE="${ECR_REGISTRY}/${IMAGE_REPO}:${IMAGE_TAG}"

# Minimum tool versions. These pins are deliberate (see docs/security-pinning.md):
# Trivy < 0.70.0 includes the compromised 0.69.4/5/6 builds; Cosign 3.0 changed the
# signing surface. Do not lower these to accommodate an older local install.
MIN_TRIVY="0.70.0"
MIN_COSIGN="3.0.0"

log() { printf '==> %s\n' "$*"; }

# Return success if $1 (found version) is >= $2 (minimum), using version sort.
version_ge() {
  [ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -n1)" = "$2" ]
}

require_versions() {
  log "Checking tool versions (trivy >= ${MIN_TRIVY}, cosign >= ${MIN_COSIGN})"
  local trivy_version cosign_version
  trivy_version="$(trivy --version | awk '/^Version:/ {print $2; exit}')"
  cosign_version="$(cosign version 2>/dev/null | awk '/GitVersion:|^Version:/ {gsub(/^v/,"",$2); print $2; exit}')"

  if [ -z "${trivy_version}" ] || ! version_ge "${trivy_version}" "${MIN_TRIVY}"; then
    echo "FATAL: trivy ${trivy_version:-<none>} is below required ${MIN_TRIVY}" >&2
    exit 1
  fi
  if [ -z "${cosign_version}" ] || ! version_ge "${cosign_version}" "${MIN_COSIGN}"; then
    echo "FATAL: cosign ${cosign_version:-<none>} is below required ${MIN_COSIGN}" >&2
    exit 1
  fi
  log "Tool versions OK (trivy ${trivy_version}, cosign ${cosign_version})"
}

main() {
  require_versions

  log "Extracting model artifact ${MODEL_ARTIFACT} into build context"
  rm -rf "${BUILD_CONTEXT}/model-build"
  mkdir -p "${BUILD_CONTEXT}/model-build"
  # The tarball contains model-v1.0.0/<files>; strip the top directory level.
  tar -xzf "${MODEL_ARTIFACT}" -C "${BUILD_CONTEXT}/model-build" --strip-components=1

  log "Building image ${IMAGE}"
  docker build -t "${IMAGE}" "${BUILD_CONTEXT}"

  log "Scanning image for HIGH/CRITICAL vulnerabilities"
  # Any HIGH or CRITICAL finding fails the build (and therefore the workflow).
  trivy image --severity HIGH,CRITICAL --exit-code 1 --no-progress "${IMAGE}"

  log "Pushing image ${IMAGE}"
  docker push "${IMAGE}"

  # Resolve the immutable digest of the pushed image and sign by digest.
  local digest image_by_digest
  digest="$(docker inspect --format='{{index .RepoDigests 0}}' "${IMAGE}" | cut -d'@' -f2)"
  if [ -z "${digest}" ]; then
    echo "FATAL: could not resolve pushed image digest" >&2
    exit 1
  fi
  image_by_digest="${ECR_REGISTRY}/${IMAGE_REPO}@${digest}"

  log "Signing ${image_by_digest} with KMS key ${KMS_KEY_ID}"
  cosign sign --yes --key "awskms://${KMS_KEY_ID}" "${image_by_digest}"

  log "Image digest: ${digest}"
  # Expose the digest to downstream jobs (verify-container, terraform).
  if [ -n "${GITHUB_OUTPUT:-}" ]; then
    echo "image_digest=${digest}" >> "${GITHUB_OUTPUT}"
  fi
}

main "$@"
