#!/usr/bin/env bash
# ABOUTME: Runs the KServe and HPA k6 ramps back-to-back, sampling pod counts throughout,
# ABOUTME: then prints time-to-scale-up, peak pod count, and time-to-scale-down for each.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="${NAMESPACE:-default}"
SAMPLE_INTERVAL="${SAMPLE_INTERVAL:-5}"

require() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: '$1' is required." >&2; exit 2; }; }
require k6
require kubectl

# Sample a pod count (matching a label selector) into a file with elapsed seconds, until
# a sentinel file appears. Runs in the background during a k6 run.
sample_pods() {
  local selector="$1" outfile="$2" stopfile="$3"
  local start now count
  start="$(date +%s)"
  : >"$outfile"
  while [[ ! -f "$stopfile" ]]; do
    now="$(date +%s)"
    count="$(kubectl get pods -n "$NAMESPACE" -l "$selector" \
      --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ')"
    echo "$((now - start)) $count" >>"$outfile"
    sleep "$SAMPLE_INTERVAL"
  done
}

# Analyze a samples file: baseline (first), peak, time to first rise, time back to baseline.
analyze() {
  local file="$1" label="$2"
  awk -v label="$label" '
    NR==1 { baseline=$2 }
    { t=$1; c=$2; if (c>peak){peak=c; peak_t=t}
      if (up=="" && c>baseline){up=t}
      if (up!="" && down=="" && c<=baseline && t>up){down=t} }
    END {
      printf "  %-22s baseline=%d  peak=%d  scale-up@=%ss  back-to-baseline@=%ss\n",
        label, baseline, peak, (up==""?"n/a":up), (down==""?"n/a":down)
    }' "$file"
}

run_case() {
  local name="$1" script="$2" selector="$3"
  local samples stop
  samples="$(mktemp)"; stop="$(mktemp -u)"
  echo "==> [$name] sampling pods (selector: $selector) while k6 runs"
  sample_pods "$selector" "$samples" "$stop" &
  local sampler_pid=$!
  k6 run "$SCRIPT_DIR/$script" || echo "  (k6 reported threshold failures — expected for the HPA baseline)"
  touch "$stop"; wait "$sampler_pid" 2>/dev/null || true
  analyze "$samples" "$name"
  rm -f "$samples"
}

echo "### Scaling comparison: KServe (concurrency) vs HPA (CPU) ###"
run_case "KServe concurrency" "k6-xgboost-kserve.js" \
  "serving.kserve.io/inferenceservice=adult-income-classifier"
run_case "HPA CPU baseline" "k6-xgboost-hpa.js" \
  "app=xgboost-hpa-baseline"

echo
echo "Read the two rows together: KServe should scale up sooner (on concurrency) and back"
echo "to zero after load; the HPA baseline lags (waits for CPU to cross 50%) and floors at 1."
