# Model Comparison Specification

## Purpose
Defines the behavior of the scheduled comparison Lambda. Implementation
at `MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/lambdas/comparison/`.

## Requirements

## ADDED Requirements

### Requirement: Scheduled Comparison
The comparison Lambda MUST run on a 5-minute EventBridge schedule and
process all shadow-log entries since the previous run.

#### Scenario: Routine run with new data
- GIVEN 1,500 shadow-log entries have been written since the last run
- WHEN the comparison Lambda fires
- THEN all 1,500 entries are joined with their challenger async outputs
- AND entries whose challenger output is not yet available are deferred
- AND a comparison summary is written to S3

### Requirement: Agreement Rate Computation
The comparison Lambda MUST compute the fraction of joined entries where
champion and challenger predicted the same label.

#### Scenario: 92% agreement
- GIVEN 1,000 joined entries with 920 matching predictions
- WHEN agreement rate is computed
- THEN the result is 0.92
- AND `ShadowAgreementRate` is emitted to CloudWatch with value 0.92

### Requirement: Latency Comparison
The comparison Lambda MUST compute p95 latency for both endpoints and
emit the delta as a CloudWatch metric.

#### Scenario: Challenger 20% slower
- GIVEN champion p95 is 100ms and challenger p95 is 120ms
- WHEN latency metrics are computed
- THEN `ShadowLatencyP95Delta` is emitted with value 20.0 (percent)

### Requirement: Disparate Impact per Protected Class
The comparison Lambda MUST compute the predicted positive rate per
protected class (sex × race) and emit each group's ratio relative to
the highest-rate group.

#### Scenario: Group ratio computation
- GIVEN four protected-class groups with predicted positive rates
  [0.50, 0.45, 0.42, 0.35]
- WHEN disparate impact is computed
- THEN each group ratio relative to 0.50 is: [1.00, 0.90, 0.84, 0.70]
- AND `ShadowDisparateImpactRatio` is emitted for each group

### Requirement: Comparison Result Schema
Every comparison run MUST write a result file to S3 with all required
fields.

#### Scenario: Result file structure
- GIVEN a comparison run completes
- WHEN the result is written to S3
- THEN the file contains: `metrics`, `criteria_evaluated`,
  `promotion_check_status`, `failure_reasons`, `evaluation_window_start`,
  `evaluation_window_end`
- AND `promotion_check_status` is `ready` if all criteria pass else
  `not_ready`
- AND `failure_reasons` lists every failed criterion with actual vs
  required values
