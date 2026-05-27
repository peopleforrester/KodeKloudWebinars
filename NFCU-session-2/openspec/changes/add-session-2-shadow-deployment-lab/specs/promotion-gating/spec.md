# Promotion Gating Specification

## Purpose
Defines the behavior of the promotion workflow. Workflow at
`.github/workflows/session-2-promote-challenger.yml` reads
`MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/config/promotion-criteria.yaml`.

## Requirements

## ADDED Requirements

### Requirement: Promotion Criteria File Schema
The repo MUST contain
`MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/config/promotion-criteria.yaml`
with this schema:

```yaml
promotion_criteria:
  agreement_rate:
    minimum: <float>
    maximum: <float>
  latency_p95_ms:
    challenger_max: <int>
    delta_vs_champion_max_pct: <int>
  disparate_impact:
    max_ratio_per_group: <float>
    must_not_be_worse_than_champion: <bool>
  minimum_observations: <int>
  minimum_observations_per_protected_group: <int>
rollback_criteria:
  post_promotion_accuracy_drop_pct: <float>
  post_promotion_error_rate_increase_pct: <float>
  evaluation_window_minutes: <int>
```

#### Scenario: Workflow reads criteria
- GIVEN the promotion workflow is triggered
- WHEN the workflow starts
- THEN it reads the promotion-criteria file and the latest comparison
  result file
- AND it evaluates each criterion against the metrics

### Requirement: Gate Refuses on Any Failure
The promotion workflow MUST refuse to flip traffic if ANY criterion fails.

#### Scenario: Agreement below minimum
- GIVEN agreement_rate.minimum is 0.85 and result shows 0.82
- WHEN the workflow runs with dry_run=false
- THEN the workflow fails with "criteria not met"
- AND the message names the criterion and actual vs required values
- AND no environment variable on the shadow-mirror Lambda is modified

### Requirement: Gate Refuses on Suspicious Agreement
The promotion workflow MUST refuse to flip if agreement_rate exceeds
agreement_rate.maximum.

#### Scenario: Agreement at 0.995
- GIVEN agreement_rate.maximum is 0.99 and result shows 0.995
- WHEN the workflow runs
- THEN the workflow fails with "criteria not met: agreement_rate 0.995
  exceeds maximum 0.99 (challenger may not be meaningfully different
  from champion)"

### Requirement: Gate Refuses on Insufficient Observations
The promotion workflow MUST refuse if minimum_observations or
minimum_observations_per_protected_group is not met.

#### Scenario: Only 500 observations
- GIVEN minimum_observations is 1000 and only 500 exist
- WHEN the workflow runs
- THEN the workflow fails with "criteria not met: 500 observations,
  minimum 1000 required"

### Requirement: Dry-Run Mode
The promotion workflow MUST accept a `dry_run` boolean input that, when
true, evaluates criteria without modifying any Lambda environment.

#### Scenario: Dry run with passing criteria
- GIVEN all criteria pass
- WHEN the workflow runs with dry_run=true
- THEN the workflow succeeds with "criteria met, promotion approved
  (dry run, no changes made)"
- AND the shadow-mirror Lambda env vars are unchanged

### Requirement: Traffic Flip Mechanism
On successful non-dry-run promotion, the workflow MUST swap
CHAMPION_ENDPOINT_ARN and CHALLENGER_ENDPOINT_ARN on the shadow-mirror
Lambda.

#### Scenario: Successful promotion
- GIVEN criteria pass and dry_run=false
- WHEN the workflow runs
- THEN CHAMPION_ENDPOINT_ARN is set to the previous
  CHALLENGER_ENDPOINT_ARN value and vice versa
- AND subsequent caller requests receive the new champion's predictions

### Requirement: Path-Filtered Workflow Triggering
The session-2-promote-challenger workflow MUST be path-filtered to
only auto-trigger from changes within
`MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/**` (workflow_dispatch
is always available).

#### Scenario: Agentic_DevOps PR does not trigger Session 2 workflows
- GIVEN a PR touches only `Agentic_DevOps/resources.md`
- WHEN the PR is opened against main
- THEN session-2-promote-challenger.yml does NOT appear in the PR's
  check runs

#### Scenario: Session 3 README change does not trigger Session 2
- GIVEN a PR touches only
  `MLOps_Deployment_Workshop/Session_3_Monitoring_Drift/README.md`
- WHEN the PR is opened
- THEN no session-2-*.yml workflow appears in the PR's check runs
