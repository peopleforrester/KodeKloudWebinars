# nfcu-session-4-load-test-harness

## ADDED Requirements

### Requirement: k6 scripts cover each lab's traffic pattern

`tests/load/` SHALL contain `k6-xgboost-kserve.js`, `k6-xgboost-hpa.js`, `k6-tinyllama.js`, `k6-canary-traffic.js`.

#### Scenario: KServe load drives concurrency-based scaling
- **GIVEN** a deployed Lab 1 InferenceService
- **WHEN** `k6 run tests/load/k6-xgboost-kserve.js` runs
- **THEN** it ramps 1→100 VUs over 2 min, holds 3 min, ramps down 1 min
- **AND** observable pod count rises during hold

#### Scenario: HPA comparison surfaces the autoscaling gap
- **GIVEN** the HPA baseline Deployment running
- **WHEN** the HPA k6 script runs with the same ramp
- **THEN** `tests/load/compare-scaling.sh` prints a side-by-side summary of time-to-scale-up and peak pod count

### Requirement: LLM load test respects concurrency limits

`k6-tinyllama.js` SHALL use a gentler ramp (1→10 VUs) that does not exceed `containerConcurrency: 5` × `maxReplicas: 3`.

#### Scenario: LLM load stays under sustained 5xx
- **GIVEN** the TinyLlama InferenceService at maxReplicas: 3
- **WHEN** the LLM k6 script runs
- **THEN** error rate stays under 1% during steady-state

### Requirement: Canary script supports statistical split observation

`k6-canary-traffic.js` SHALL drive 5 RPS for 5 minutes — enough to observe the split, not enough to trigger autoscaling beyond minReplicas.

#### Scenario: Split is statistically observable
- **GIVEN** a canary at 10% to v1.0.1
- **WHEN** the canary traffic script completes
- **THEN** 8–12% of requests landed on v1.0.1
- **AND** per-revision counts appear in the k6 summary

### Requirement: Smoke tests precede load tests

`tests/smoke/curl-tests.sh` SHALL send one successful prediction to each endpoint before any load test.

#### Scenario: Smoke catches deploy failures fast
- **GIVEN** a deployed InferenceService
- **WHEN** smoke runs
- **THEN** within 5 seconds either all endpoints return 200, or the script exits non-zero naming the failed endpoint
