# Runbook: Latency Degradation

> **Routing rule — read first.**
> **If fixing requires understanding the model → page the model owner.**
> **If fixing uses infrastructure tools → DevOps handles.**

| Field | Value |
|-------|-------|
| Expected alarm/signal | `Latency-P95-{attendee_id}` (p95 > 500ms) |
| First responder | DevOps |
| Severity | Sev2 |

Inference latency climbs while predictions stay correct. This is a pure
infrastructure incident — capacity, noisy neighbors, or a slow dependency.
**DevOps almost always** owns this end to end.

## Detection

- `Latency-P95-{attendee_id}` in ALARM (p95 ModelLatency > 500ms; note SageMaker
  reports ModelLatency in microseconds, so the threshold is 500000).
- Prediction quality signals (PSI, NannyML estimate) are unchanged — correctness
  is fine, speed is not.

## Triage

- Check invocation volume and concurrency — is this a load spike?
  ```bash
  aws cloudwatch get-metric-statistics --namespace AWS/SageMaker \
    --metric-name Invocations --statistics Sum --period 60 \
    --dimensions Name=EndpointName,Value=workshop-lab-{attendee_id}-production Name=VariantName,Value=AllTraffic \
    --start-time "$(date -u -d '30 min ago' +%FT%TZ)" --end-time "$(date -u +%FT%TZ)"
  ```
- Check instance health / saturation (CPU, memory) and whether a co-located
  workload is competing (noisy neighbor).
- Check downstream dependency latency (feature lookups, external calls).
- Correlate with recent deploys or instance-type changes.

## Decision

- Apply the routing rule. Latency is fixed with **infrastructure tools** (scale,
  reschedule, revert) → **DevOps handles**. The model owner is generally not
  involved unless triage shows a model-side change (e.g., a heavier model variant)
  caused the slowdown.

## Containment

- Scale out / up the endpoint variant, or roll back to the previous endpoint
  config if a recent change introduced the latency:
  ```bash
  aws sagemaker update-endpoint --endpoint-name workshop-lab-{attendee_id}-production \
    --endpoint-config-name <previous-config>
  ```

## Resolution

- Confirm p95 returns below 500ms and the alarm clears. Right-size capacity or fix
  the slow dependency permanently. Add a follow-up if autoscaling thresholds need
  tuning to absorb the observed load pattern.
