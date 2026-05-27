#!/usr/bin/env bash
# ABOUTME: Pre-session readiness check across all attendee sandboxes, in parallel.
# ABOUTME: Prints a green/red table; red rows name the specific failure mode.
set -euo pipefail

# ---------------------------------------------------------------------------
# For each attendee, verify: endpoint InService, exactly three alarms, and the
# CloudWatch dashboard exists. Runs checks in parallel and prints a status table.
# Exit code: 0 if all green, 1 if any red.
# ---------------------------------------------------------------------------

REGION="us-east-1"
COHORT_FILE=""
PARALLELISM=10
declare -a ATTENDEES=()

usage() {
  cat <<EOF
Usage: $0 (--cohort <file> | --attendee-id <id> [--attendee-id <id> ...]) [options]
  --cohort <file>        File with one attendee_id per line
  --attendee-id <id>     Add a single attendee (repeatable)
  --region <region>      AWS region (default: ${REGION})
  --parallelism <n>      Concurrent checks (default: ${PARALLELISM})
  -h, --help             Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cohort) COHORT_FILE="$2"; shift 2 ;;
    --attendee-id) ATTENDEES+=("$2"); shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --parallelism) PARALLELISM="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -n "$COHORT_FILE" ]]; then
  [[ -f "$COHORT_FILE" ]] || { echo "ERROR: cohort file not found: $COHORT_FILE" >&2; exit 2; }
  while IFS= read -r line; do
    line="$(echo "$line" | tr -d '[:space:]')"
    [[ -n "$line" ]] && ATTENDEES+=("$line")
  done < "$COHORT_FILE"
fi

[[ ${#ATTENDEES[@]} -gt 0 ]] || { echo "ERROR: no attendees provided" >&2; usage; exit 2; }

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

# Check one attendee; write "id<TAB>STATUS<TAB>detail" to a per-attendee file.
check_attendee() {
  local id="$1" region="$2" out="$3"
  local endpoint="workshop-lab-${id}-production"

  local status
  status="$(aws sagemaker describe-endpoint --endpoint-name "$endpoint" --region "$region" \
    --query 'EndpointStatus' --output text 2>/dev/null || echo "MISSING")"
  if [[ "$status" != "InService" ]]; then
    printf '%s\tRED\tendpoint %s (status: %s)\n' "$id" \
      "$([[ "$status" == MISSING ]] && echo missing || echo unhealthy)" "$status" > "$out"
    return
  fi

  # Count all three expected alarms by their distinct prefixes.
  local total=0 n
  for prefix in "Drift-PSI-${id}" "Latency-P95-${id}" "ErrorRate-${id}"; do
    n="$(aws cloudwatch describe-alarms --alarm-name-prefix "$prefix" --region "$region" \
      --query 'length(MetricAlarms)' --output text 2>/dev/null || echo 0)"
    total=$(( total + n ))
  done
  if [[ "$total" -ne 3 ]]; then
    printf '%s\tRED\talarm misconfigured (found %s of 3)\n' "$id" "$total" > "$out"
    return
  fi

  if ! aws cloudwatch get-dashboard --dashboard-name "workshop-lab-${id}" --region "$region" \
      >/dev/null 2>&1; then
    printf '%s\tRED\tdashboard not provisioned\n' "$id" > "$out"
    return
  fi

  printf '%s\tGREEN\tendpoint InService, 3 alarms, dashboard present\n' "$id" > "$out"
}
export -f check_attendee

# Fan out with bounded parallelism. Single quotes are intentional: $1/$2/$3 are
# positional args to the inner shell, not parent-shell expansions.
# shellcheck disable=SC2016
printf '%s\n' "${ATTENDEES[@]}" | \
  xargs -P "$PARALLELISM" -I {} bash -c 'check_attendee "$1" "$2" "$3/$1.txt"' _ {} "$REGION" "$WORKDIR"

# Collate and print the table.
printf '\n%-16s %-6s %s\n' "ATTENDEE" "STATUS" "DETAIL"
printf '%-16s %-6s %s\n' "----------------" "------" "------------------------------------------"
red=0
while IFS= read -r id; do
  if [[ -f "$WORKDIR/$id.txt" ]]; then
    IFS=$'\t' read -r aid st detail < "$WORKDIR/$id.txt"
    printf '%-16s %-6s %s\n' "$aid" "$st" "$detail"
    [[ "$st" == "RED" ]] && red=$(( red + 1 ))
  else
    printf '%-16s %-6s %s\n' "$id" "RED" "check did not complete"
    red=$(( red + 1 ))
  fi
done < <(printf '%s\n' "${ATTENDEES[@]}")

printf '\n%d attendees, %d red.\n' "${#ATTENDEES[@]}" "$red"
[[ "$red" -eq 0 ]]
