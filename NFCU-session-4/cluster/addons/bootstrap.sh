#!/usr/bin/env bash
# ABOUTME: Idempotent, dependency-ordered installer for the Session 4 cluster add-ons.
# ABOUTME: Usage: bootstrap.sh <eks|local>. Same script for both cluster paths.
set -euo pipefail

# ---------------------------------------------------------------------------
# Pinned versions — single source of truth. Mirror these in helm-values/*.yaml
# headers. See cluster/addons/README.md for why each is pinned where it is.
# ---------------------------------------------------------------------------
CERT_MANAGER_VERSION="v1.16.1"
KNATIVE_VERSION="knative-v1.15.2"
KOURIER_VERSION="knative-v1.15.0"
KSERVE_VERSION="v0.16.0"
KPS_CHART_VERSION="85.3.3"      # kube-prometheus-stack
OPENCOST_CHART_VERSION="2.5.21"
ALB_CHART_VERSION="3.3.0"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALUES="$SCRIPT_DIR/helm-values"
TF_DIR="$SCRIPT_DIR/../eks/terraform"

# ---------------------------------------------------------------------------
ENVIRONMENT="${1:-}"
if [[ "$ENVIRONMENT" != "eks" && "$ENVIRONMENT" != "local" ]]; then
  echo "Usage: $0 <eks|local>" >&2
  exit 2
fi

log() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }
die() { printf '\033[31mERROR: add-on "%s" did not become ready. Stopping; later add-ons not installed.\033[0m\n' "$1" >&2; exit 1; }

# Wait for all Deployments in a namespace to be Available, or fail naming the component.
wait_ns() {
  local ns="$1" component="$2" timeout="${3:-300s}"
  kubectl rollout status deployment --namespace "$ns" --timeout="$timeout" 2>/dev/null \
    || kubectl wait --for=condition=Available deployment --all -n "$ns" --timeout="$timeout" \
    || die "$component"
}

require() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: '$1' is required but not installed." >&2; exit 2; }; }
require kubectl
require helm

# ---------------------------------------------------------------------------
log "Adding/refreshing Helm repos"
helm repo add jetstack https://charts.jetstack.io >/dev/null
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo add opencost https://opencost.github.io/opencost-helm-chart >/dev/null
[[ "$ENVIRONMENT" == "eks" ]] && helm repo add eks https://aws.github.io/eks-charts >/dev/null
helm repo update >/dev/null

# ---------------------------------------------------------------------------
# 1. cert-manager
# ---------------------------------------------------------------------------
log "[1] cert-manager $CERT_MANAGER_VERSION"
helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --version "$CERT_MANAGER_VERSION" \
  -f "$VALUES/cert-manager.yaml" --wait --timeout 5m || die "cert-manager"
wait_ns cert-manager cert-manager

# ---------------------------------------------------------------------------
# 2. Knative Serving (release YAML) + autoscaler config patch
# ---------------------------------------------------------------------------
log "[2] Knative Serving $KNATIVE_VERSION"
kubectl apply -f "https://github.com/knative/serving/releases/download/${KNATIVE_VERSION}/serving-crds.yaml"
kubectl apply -f "https://github.com/knative/serving/releases/download/${KNATIVE_VERSION}/serving-core.yaml"
wait_ns knative-serving "Knative Serving"
kubectl apply -f "$VALUES/knative-serving.yaml"

# ---------------------------------------------------------------------------
# 3. AWS Load Balancer Controller (EKS only) — installed before Kourier so the
#    NLB exists when Kourier's LoadBalancer Service is created.
# ---------------------------------------------------------------------------
if [[ "$ENVIRONMENT" == "eks" ]]; then
  log "[3] AWS Load Balancer Controller $ALB_CHART_VERSION (EKS)"
  CLUSTER_NAME="$(terraform -chdir="$TF_DIR" output -raw cluster_name 2>/dev/null || echo "nfcu-session-4")"
  ALB_ROLE_ARN="$(terraform -chdir="$TF_DIR" output -raw alb_controller_role_arn 2>/dev/null || true)"
  [[ -z "$ALB_ROLE_ARN" ]] && die "aws-load-balancer-controller (could not read IRSA role ARN from terraform output)"
  helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
    --namespace kube-system \
    --version "$ALB_CHART_VERSION" \
    -f "$VALUES/aws-load-balancer-controller.yaml" \
    --set "clusterName=${CLUSTER_NAME}" \
    --set "serviceAccount.annotations.eks\.amazonaws\.com/role-arn=${ALB_ROLE_ARN}" \
    --wait --timeout 5m || die "aws-load-balancer-controller"
  wait_ns kube-system "aws-load-balancer-controller"
else
  log "[3] AWS Load Balancer Controller — skipped (local kind has no AWS NLB)"
fi

# ---------------------------------------------------------------------------
# 4. Kourier (release YAML) + ingress-class patch
# ---------------------------------------------------------------------------
log "[4] Kourier $KOURIER_VERSION"
kubectl apply -f "https://github.com/knative/net-kourier/releases/download/${KOURIER_VERSION}/kourier.yaml"
wait_ns kourier-system Kourier
kubectl apply -f "$VALUES/kourier.yaml"

if [[ "$ENVIRONMENT" == "local" ]]; then
  # Expose Kourier on a fixed NodePort that the kind port mapping forwards (see
  # cluster/local/kind-config.yaml: hostPort 31080 -> containerPort 31080).
  kubectl patch -n kourier-system service kourier \
    --type merge \
    -p '{"spec":{"type":"NodePort","ports":[{"name":"http2","port":80,"targetPort":8080,"nodePort":31080}]}}'
fi

# ---------------------------------------------------------------------------
# 5. KServe (CRDs + controller)
# ---------------------------------------------------------------------------
log "[5] KServe $KSERVE_VERSION"
helm upgrade --install kserve-crd "oci://ghcr.io/kserve/charts/kserve-crd" \
  --namespace kserve --create-namespace \
  --version "$KSERVE_VERSION" --wait --timeout 5m || die "kserve-crd"
helm upgrade --install kserve "oci://ghcr.io/kserve/charts/kserve-resources" \
  --namespace kserve \
  --version "$KSERVE_VERSION" \
  -f "$VALUES/kserve.yaml" --wait --timeout 5m || die "kserve"
wait_ns kserve KServe

# ---------------------------------------------------------------------------
# 6. kube-prometheus-stack
# ---------------------------------------------------------------------------
log "[6] kube-prometheus-stack $KPS_CHART_VERSION"
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --version "$KPS_CHART_VERSION" \
  -f "$VALUES/kube-prometheus-stack.yaml" --wait --timeout 8m || die "kube-prometheus-stack"
wait_ns monitoring "kube-prometheus-stack"

# ---------------------------------------------------------------------------
# 7. OpenCost
# ---------------------------------------------------------------------------
log "[7] OpenCost $OPENCOST_CHART_VERSION"
helm upgrade --install opencost opencost/opencost \
  --namespace opencost --create-namespace \
  --version "$OPENCOST_CHART_VERSION" \
  -f "$VALUES/opencost.yaml" --wait --timeout 5m || die "opencost"
wait_ns opencost OpenCost

log "All add-ons installed. Verify with: bash $SCRIPT_DIR/verify.sh"
