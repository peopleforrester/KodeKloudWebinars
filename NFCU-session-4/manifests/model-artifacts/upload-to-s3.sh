#!/usr/bin/env bash
# ABOUTME: Uploads the generated XGBoost model artifacts to the Terraform-created S3 bucket.
# ABOUTME: Reads the bucket name from `terraform output` so it always targets the right one.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$SCRIPT_DIR/../../cluster/eks/terraform"

require() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: '$1' is required but not installed." >&2; exit 2; }; }
require aws
require terraform

BUCKET="$(terraform -chdir="$TF_DIR" output -raw model_artifacts_bucket_name 2>/dev/null || true)"
if [[ -z "$BUCKET" ]]; then
  echo "ERROR: could not read model_artifacts_bucket_name from terraform output." >&2
  echo "Provision the EKS cluster first (cluster/eks/up.sh), or pass a bucket via S3_BUCKET=." >&2
  BUCKET="${S3_BUCKET:-}"
  [[ -z "$BUCKET" ]] && exit 1
fi

for version in model-v1.0.0 model-v1.0.1; do
  src="$SCRIPT_DIR/$version"
  if [[ ! -f "$src/model.bst" ]]; then
    echo "ERROR: $src/model.bst not found. Run generate-xgboost-models.py first." >&2
    exit 1
  fi
  echo "==> Uploading $version to s3://$BUCKET/$version/"
  aws s3 cp "$src/" "s3://$BUCKET/$version/" --recursive
done

echo "Done. The Lab 1/4 manifests' storageUri should be:  s3://$BUCKET/model-v1.0.0  (and …v1.0.1)"
