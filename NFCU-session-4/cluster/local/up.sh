#!/usr/bin/env bash
# ABOUTME: Creates the local kind cluster and installs all add-ons for laptop rehearsal.
# ABOUTME: No AWS spend. Idempotent — re-running reuses the existing cluster.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTER_NAME="nfcu-session-4"
CONFIG="$SCRIPT_DIR/kind-config.yaml"
BOOTSTRAP="$SCRIPT_DIR/../addons/bootstrap.sh"

require() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: '$1' is required but not installed." >&2; exit 2; }; }
require kind
require kubectl
require helm
require docker

if kind get clusters 2>/dev/null | grep -qx "$CLUSTER_NAME"; then
  echo "==> kind cluster '$CLUSTER_NAME' already exists; reusing it."
else
  echo "==> Creating kind cluster '$CLUSTER_NAME' (1 control-plane + 2 workers)"
  kind create cluster --config "$CONFIG" --wait 120s
fi

# kind sets the kubectl context to kind-<name>.
kubectl config use-context "kind-${CLUSTER_NAME}" >/dev/null

echo "==> Installing add-ons (this takes ~10-15 min on first run)"
bash "$BOOTSTRAP" local

echo "==> Verifying"
bash "$SCRIPT_DIR/../addons/verify.sh"

cat <<EOF

Local cluster '$CLUSTER_NAME' is ready.
  - Ingress (Kourier) is reachable at http://localhost:31080
  - Deploy a lab:   kubectl apply -f manifests/lab1-xgboost-inferenceservice.yaml -n <ns>
  - Tear it down:   bash $SCRIPT_DIR/down.sh
EOF
