#!/usr/bin/env bash
# ABOUTME: Destroys the local kind cluster and prunes the Docker artifacts it created.
# ABOUTME: Only touches resources for this named cluster — safe to run anytime.
set -euo pipefail

CLUSTER_NAME="nfcu-session-4"

require() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: '$1' is required but not installed." >&2; exit 2; }; }
require kind

if kind get clusters 2>/dev/null | grep -qx "$CLUSTER_NAME"; then
  echo "==> Deleting kind cluster '$CLUSTER_NAME'"
  kind delete cluster --name "$CLUSTER_NAME"
else
  echo "==> No kind cluster named '$CLUSTER_NAME'; nothing to delete."
fi

# kind runs each node as a Docker container named "<cluster>-control-plane" etc., and
# `kind delete` removes them. Clean up any stragglers from a half-created cluster.
if command -v docker >/dev/null 2>&1; then
  STRAGGLERS="$(docker ps -aq --filter "name=^${CLUSTER_NAME}-" 2>/dev/null || true)"
  if [[ -n "$STRAGGLERS" ]]; then
    echo "==> Removing leftover kind node containers"
    docker rm -f $STRAGGLERS >/dev/null
  fi
fi

echo "==> Done. Verify with: kind get clusters"
