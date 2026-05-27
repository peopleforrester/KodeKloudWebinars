#!/usr/bin/env bash
# ABOUTME: Idempotently restore an attendee's Session 1/2 SageMaker endpoint.
# ABOUTME: Fast no-op if InService; else recreate from the baseline artifact (<=4 min).
set -euo pipefail

# ---------------------------------------------------------------------------
# Restore the Session 1/2 production endpoint for one attendee (design D8).
#   - If the endpoint is already InService: exit 0 in <10s (no modification).
#   - Otherwise: (re)create it from the baseline model artifact and wait for
#     InService. Target end-to-end budget: <= 4 minutes.
# Safe to run repeatedly during the pre-flight window.
# ---------------------------------------------------------------------------

REGION="us-east-1"
ATTENDEE_ID=""
ARTIFACT_S3=""                       # s3://.../model.tar.gz (see Open Question 3)
ROLE_ARN="${SAGEMAKER_EXEC_ROLE_ARN:-}"
INSTANCE_TYPE="ml.m5.xlarge"
# Region-specific SageMaker managed sklearn inference image (us-east-1 default).
SKLEARN_IMAGE="${SAGEMAKER_SKLEARN_IMAGE:-683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.2-1}"

usage() {
  cat <<EOF
Usage: $0 --attendee-id <id> [options]
  --attendee-id <id>     Required. e.g. lab-007
  --region <region>      AWS region (default: ${REGION})
  --artifact-s3 <uri>    s3:// URI of model.tar.gz (default: derived shared bucket)
  --role-arn <arn>       SageMaker execution role ARN (or env SAGEMAKER_EXEC_ROLE_ARN)
  --instance-type <t>    Endpoint instance type (default: ${INSTANCE_TYPE})
  -h, --help             Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --attendee-id) ATTENDEE_ID="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --artifact-s3) ARTIFACT_S3="$2"; shift 2 ;;
    --role-arn) ROLE_ARN="$2"; shift 2 ;;
    --instance-type) INSTANCE_TYPE="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

[[ -n "$ATTENDEE_ID" ]] || { echo "ERROR: --attendee-id is required" >&2; usage; exit 2; }

ENDPOINT_NAME="workshop-lab-${ATTENDEE_ID}-production"
: "${ARTIFACT_S3:=s3://kodekloud-mlops-shared-artifacts-${REGION}/nfcu-session-3/baseline-model/model.tar.gz}"
START=$(date +%s)

log() { printf '[restore %s | +%ss] %s\n' "$ATTENDEE_ID" "$(( $(date +%s) - START ))" "$*"; }

endpoint_status() {
  aws sagemaker describe-endpoint --endpoint-name "$ENDPOINT_NAME" --region "$REGION" \
    --query 'EndpointStatus' --output text 2>/dev/null || echo "MISSING"
}

# --- Fast path: already healthy -------------------------------------------
STATUS="$(endpoint_status)"
log "current endpoint status: ${STATUS}"
if [[ "$STATUS" == "InService" ]]; then
  log "endpoint already InService — no-op."
  exit 0
fi

[[ -n "$ROLE_ARN" ]] || { echo "ERROR: --role-arn or SAGEMAKER_EXEC_ROLE_ARN required to (re)create" >&2; exit 2; }

# --- Clean up a failed/partial endpoint before recreating ------------------
if [[ "$STATUS" != "MISSING" && "$STATUS" != "Creating" ]]; then
  log "deleting endpoint in state ${STATUS} before recreating"
  aws sagemaker delete-endpoint --endpoint-name "$ENDPOINT_NAME" --region "$REGION" || true
  aws sagemaker wait endpoint-deleted --endpoint-name "$ENDPOINT_NAME" --region "$REGION" 2>/dev/null || true
fi

SUFFIX="$(date +%Y%m%d%H%M%S)"
MODEL_NAME="${ENDPOINT_NAME}-model-${SUFFIX}"
CONFIG_NAME="${ENDPOINT_NAME}-config-${SUFFIX}"

log "creating model ${MODEL_NAME} from ${ARTIFACT_S3}"
aws sagemaker create-model \
  --model-name "$MODEL_NAME" \
  --region "$REGION" \
  --execution-role-arn "$ROLE_ARN" \
  --primary-container "Image=${SKLEARN_IMAGE},ModelDataUrl=${ARTIFACT_S3},Environment={SAGEMAKER_PROGRAM=inference.py,SAGEMAKER_SUBMIT_DIRECTORY=${ARTIFACT_S3}}" \
  >/dev/null

log "creating endpoint config ${CONFIG_NAME} (${INSTANCE_TYPE})"
aws sagemaker create-endpoint-config \
  --endpoint-config-name "$CONFIG_NAME" \
  --region "$REGION" \
  --production-variants "VariantName=AllTraffic,ModelName=${MODEL_NAME},InitialInstanceCount=1,InstanceType=${INSTANCE_TYPE},InitialVariantWeight=1.0" \
  >/dev/null

if [[ "$STATUS" == "MISSING" ]]; then
  log "creating endpoint ${ENDPOINT_NAME}"
  aws sagemaker create-endpoint --endpoint-name "$ENDPOINT_NAME" \
    --endpoint-config-name "$CONFIG_NAME" --region "$REGION" >/dev/null
else
  log "updating endpoint ${ENDPOINT_NAME} to new config"
  aws sagemaker update-endpoint --endpoint-name "$ENDPOINT_NAME" \
    --endpoint-config-name "$CONFIG_NAME" --region "$REGION" >/dev/null
fi

log "waiting for InService (budget: 4 min)..."
aws sagemaker wait endpoint-in-service --endpoint-name "$ENDPOINT_NAME" --region "$REGION"

# --- Smoke test: the endpoint returns a prediction ------------------------
log "smoke-testing a prediction"
TMP_OUT="$(mktemp)"
trap 'rm -f "$TMP_OUT"' EXIT
aws sagemaker-runtime invoke-endpoint \
  --endpoint-name "$ENDPOINT_NAME" --region "$REGION" \
  --content-type "text/csv" \
  --body "39,State-gov,13,Never-married,Adm-clerical,White,Male,40" \
  "$TMP_OUT" >/dev/null
log "prediction response: $(tr -d '\n' < "$TMP_OUT")"

ELAPSED=$(( $(date +%s) - START ))
log "endpoint InService and serving. Total ${ELAPSED}s."
[[ "$ELAPSED" -le 240 ]] || log "WARNING: exceeded the 4-minute budget (${ELAPSED}s) — investigate before session day."
