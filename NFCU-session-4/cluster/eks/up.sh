#!/usr/bin/env bash
# ABOUTME: Provisions the Session 4 EKS demo cluster via Terraform, then points kubectl
# ABOUTME: at it and prints the next command to bootstrap the cluster add-ons.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$SCRIPT_DIR/terraform"
ADDONS="$SCRIPT_DIR/../addons/bootstrap.sh"

if [[ ! -f "$TF_DIR/terraform.tfvars" ]]; then
  echo "ERROR: $TF_DIR/terraform.tfvars not found." >&2
  echo "Copy the example first:  cp $TF_DIR/terraform.tfvars.example $TF_DIR/terraform.tfvars" >&2
  exit 1
fi

echo "==> terraform init"
terraform -chdir="$TF_DIR" init -input=false

echo "==> terraform plan"
terraform -chdir="$TF_DIR" plan -input=false -out=tfplan

echo "==> terraform apply (this typically takes 15-25 minutes for EKS)"
terraform -chdir="$TF_DIR" apply -input=false tfplan
rm -f "$TF_DIR/tfplan"

REGION="$(terraform -chdir="$TF_DIR" output -raw region)"
CLUSTER="$(terraform -chdir="$TF_DIR" output -raw cluster_name)"

echo "==> Updating kubeconfig"
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER"

cat <<EOF

Cluster '$CLUSTER' is up in $REGION.

Next steps:
  1. Bootstrap the cluster add-ons:
       bash $ADDONS eks
  2. Upload model artifacts to S3:
       bash $SCRIPT_DIR/../../manifests/model-artifacts/upload-to-s3.sh
  3. Tear down when finished (avoids ongoing charges):
       bash $SCRIPT_DIR/down.sh
EOF
