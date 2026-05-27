#!/usr/bin/env bash
# ABOUTME: Verify an attendee's champion and challenger endpoints are InService.
# ABOUTME: Exits non-zero if either endpoint is not InService.
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

attendee="${1:?usage: verify-endpoints.sh <attendee-id>}"

check() {
  local name="$1"
  local status
  status=$(aws sagemaker describe-endpoint --endpoint-name "$name" \
    --query EndpointStatus --output text 2>/dev/null || echo "Missing")
  echo "${name}: ${status}"
  [[ "$status" == "InService" ]]
}

ok=0
check "workshop-lab-${attendee}-production" || ok=1
check "workshop-lab-${attendee}-challenger" || ok=1
exit "$ok"
