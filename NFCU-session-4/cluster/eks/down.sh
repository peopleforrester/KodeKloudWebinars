#!/usr/bin/env bash
# ABOUTME: Safety-gated teardown of the Session 4 EKS cluster. Requires the operator to
# ABOUTME: type the exact cluster name before terraform destroy runs.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$SCRIPT_DIR/terraform"

# Determine the cluster name from state if available, else from the tfvars default.
CLUSTER="$(terraform -chdir="$TF_DIR" output -raw cluster_name 2>/dev/null || true)"
if [[ -z "$CLUSTER" ]]; then
  CLUSTER="$(terraform -chdir="$TF_DIR" output -raw cluster_name 2>/dev/null || echo "nfcu-session-4")"
fi

echo "This will PERMANENTLY DESTROY the EKS cluster and all its resources."
echo "Cluster: $CLUSTER"
echo
read -r -p "Type the cluster name to confirm: " CONFIRM

if [[ "$CONFIRM" != "$CLUSTER" ]]; then
  echo "Name did not match ('$CONFIRM' != '$CLUSTER'). Aborting — nothing destroyed." >&2
  exit 1
fi

echo "==> terraform destroy"
terraform -chdir="$TF_DIR" destroy -input=false -auto-approve

echo
echo "Teardown complete. Verify with:"
echo "  aws eks list-clusters --region \$(terraform -chdir=\"$TF_DIR\" output -raw region 2>/dev/null || echo us-east-1)"
