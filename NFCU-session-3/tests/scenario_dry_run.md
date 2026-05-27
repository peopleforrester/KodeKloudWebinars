# Incident Scenario Dry-Run

**Verification method:** Scenario *logic* (round-robin assignment, dispatch,
trigger/cleanup side effects) is verified locally with stub AWS clients in
`test_incident_simulator_round_robin.py`. Firing real alarms and confirming
auto-cleanup against a live sandbox is **deferred** to the June 11 dry-run (see
`../RUN_CONFIG.md`); the table below is filled in then.

Each scenario auto-cleans up after **15 minutes** (`CLEANUP_AFTER_MINUTES`), and a
control marker under `incident-control/` in the drift-reports bucket makes cleanup
idempotent.

## Scenarios

| # | Scenario | Mechanism | Expected signal | Cleanup |
|---|----------|-----------|-----------------|---------|
| 1 | feature_pipeline_broken | Sends ~600 null-`workclass` payloads | `Drift-PSI-{id}` (workclass) | Burst ends; marker cleared |
| 2 | data_drift | Async-invokes `drift-simulator-{id}` | `Drift-PSI-{id}` (hours_per_week) | Simulator self-terminates (5 min) |
| 3 | prediction_drift_isolated | Endpoint-config swap to inverted variant (OQ4 alt) | `Drift-PSI-{id}` (prediction dist) | Revert to baseline endpoint config |
| 4 | latency_degradation | Endpoint-config swap to slow (+800ms) variant | `Latency-P95-{id}` | Revert to baseline endpoint config |
| 5 | concept_drift_confirmed | Pushes synthetic labels, 20% disagreement (D6) | NannyML `EstimatedAUCDelta` (no alarm) | Delete synthetic labels |

## Dry-run verification table (June 11)

| # | Scenario | Alarm fired? | Time to fire | Auto-cleanup verified? | Residual state? | Notes |
|---|----------|--------------|--------------|------------------------|-----------------|-------|
| 1 | feature_pipeline_broken | _pending_ | — | _pending_ | _pending_ | screenshot: _pending_ |
| 2 | data_drift | _pending_ | — | _pending_ | _pending_ | |
| 3 | prediction_drift_isolated | _pending_ | — | _pending_ | _pending_ | confirm OQ4 variant approach in sandbox |
| 4 | latency_degradation | _pending_ | — | _pending_ | _pending_ | |
| 5 | concept_drift_confirmed | n/a (signal) | — | _pending_ | _pending_ | confirm AUC delta > 0.01 |

## OQ4 note (scenario 3)

Implemented as a **SageMaker endpoint-config swap** to a session-3-owned inverted
variant, not an env-var flip in the S1/2 container (which would breach the touch
boundary). Confirm in the sandbox that both the inverted and baseline endpoint
configs exist before the session; pass their names via the
`INVERTED_ENDPOINT_CONFIG` / `BASELINE_ENDPOINT_CONFIG` env vars.
