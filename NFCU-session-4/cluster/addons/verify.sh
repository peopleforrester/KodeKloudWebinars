#!/usr/bin/env bash
# ABOUTME: Gate before lab work — confirms every add-on's Deployments are Available.
# ABOUTME: Exits non-zero naming the FIRST component that is not ready.
set -uo pipefail

require() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: '$1' required." >&2; exit 2; }; }
require kubectl

# component : namespace pairs, in install order.
COMPONENTS=(
  "cert-manager:cert-manager"
  "Knative Serving:knative-serving"
  "Kourier:kourier-system"
  "KServe:kserve"
  "kube-prometheus-stack:monitoring"
  "OpenCost:opencost"
)

FAIL=""
printf '%-26s %-18s %s\n' "COMPONENT" "NAMESPACE" "STATUS"
printf '%-26s %-18s %s\n' "---------" "---------" "------"

for entry in "${COMPONENTS[@]}"; do
  name="${entry%%:*}"
  ns="${entry##*:}"

  if ! kubectl get namespace "$ns" >/dev/null 2>&1; then
    printf '%-26s %-18s \033[31m%s\033[0m\n' "$name" "$ns" "MISSING (namespace absent)"
    [[ -z "$FAIL" ]] && FAIL="$name"
    continue
  fi

  # A component is ready when it has at least one Deployment and all are Available.
  total="$(kubectl get deploy -n "$ns" --no-headers 2>/dev/null | wc -l | tr -d ' ')"
  if [[ "$total" == "0" ]]; then
    printf '%-26s %-18s \033[31m%s\033[0m\n' "$name" "$ns" "NOT READY (no deployments)"
    [[ -z "$FAIL" ]] && FAIL="$name"
    continue
  fi

  not_ready="$(kubectl get deploy -n "$ns" \
    -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.status.availableReplicas}{"/"}{.spec.replicas}{"\n"}{end}' 2>/dev/null \
    | awk '{split($2,a,"/"); if (a[1]=="" || a[1]<a[2]) print $1}')"

  if [[ -n "$not_ready" ]]; then
    printf '%-26s %-18s \033[31m%s\033[0m\n' "$name" "$ns" "NOT READY ($(echo "$not_ready" | tr '\n' ',' | sed 's/,$//'))"
    [[ -z "$FAIL" ]] && FAIL="$name"
  else
    printf '%-26s %-18s \033[32m%s\033[0m\n' "$name" "$ns" "Ready"
  fi
done

echo
if [[ -n "$FAIL" ]]; then
  echo "FAILED: '$FAIL' is not ready. Resolve it before starting lab work (see runbook/troubleshooting-matrix.md)." >&2
  exit 1
fi
echo "All add-ons Ready."
