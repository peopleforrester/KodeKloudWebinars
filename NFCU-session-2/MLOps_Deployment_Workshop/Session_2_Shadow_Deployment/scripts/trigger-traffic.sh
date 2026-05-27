#!/usr/bin/env bash
# ABOUTME: Invoke an attendee's traffic-generator Lambda to drive shadow traffic.
# ABOUTME: Usage: trigger-traffic.sh <attendee-id> [duration_minutes] [rate].
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

attendee="${1:?usage: trigger-traffic.sh <attendee-id> [duration_minutes] [rate]}"
duration="${2:-5}"
rate="${3:-10}"

payload=$(printf '{"duration_minutes": %s, "rate": %s}' "$duration" "$rate")
out=$(mktemp)
aws lambda invoke \
  --function-name "traffic-generator-${attendee}" \
  --payload "$payload" \
  --cli-binary-format raw-in-base64-out \
  "$out" >/dev/null

echo "traffic-generator-${attendee} summary:"
cat "$out"
echo
rm -f "$out"
