# Audit Trail Specification

## Purpose
Defines the audit trail emitted by promotion and rollback events. The
audit bucket is provisioned by the shared module
`shared/terraform-modules/audit_trail/` and consumed by Session 2 (and
later Session 3).

## Requirements

## ADDED Requirements

### Requirement: Promotion Audit Entry
Every successful non-dry-run promotion MUST emit a JSON audit entry to
the attendee's audit bucket within 30 seconds of the traffic flip.

#### Scenario: Successful promotion produces audit entry
- GIVEN a promotion workflow completes successfully
- WHEN 30 seconds have passed
- THEN an object exists at
  `s3://workshop-lab-{attendee-id}-audit/audit/YYYY-MM-DD/{event-id}.json`
- AND the object contains: `event_type: "promotion_completed"`,
  `timestamp`, `actor`, `previous_champion_endpoint_arn`,
  `new_champion_endpoint_arn`, `criteria_snapshot`, `workflow_run_url`,
  `git_commit_sha`

### Requirement: Rollback Audit Entry
Every rollback MUST emit a JSON audit entry with the same schema but
`event_type: "rollback_completed"`.

#### Scenario: Rollback produces audit entry
- GIVEN a rollback workflow completes
- WHEN it finishes
- THEN an audit entry with `event_type: "rollback_completed"` exists
- AND `new_champion_endpoint_arn` equals the
  `previous_champion_endpoint_arn` from the preceding promotion entry

### Requirement: Criteria Snapshot Includes Evaluated Metrics
The `criteria_snapshot` field MUST include both the full content of
promotion-criteria.yaml at the time of the event AND the metrics that
were evaluated against it.

#### Scenario: Snapshot completeness
- GIVEN a promotion audit entry exists
- WHEN inspected
- THEN `criteria_snapshot.thresholds` matches the promotion-criteria
  file content at promotion time
- AND `criteria_snapshot.evaluated_metrics` contains the metrics values
  the gate used

### Requirement: Audit Bucket Versioning
The audit bucket MUST have S3 versioning enabled.

#### Scenario: Versioning verification
- GIVEN the audit bucket has been provisioned
- WHEN `aws s3api get-bucket-versioning` is called
- THEN the response shows `Status: Enabled`

### Requirement: Audit Bucket Survives Teardown
`scripts/teardown-attendee.sh` MUST NOT destroy the audit bucket or its
contents.

#### Scenario: Teardown preserves audit
- GIVEN attendee `dan` ran labs and triggered a promotion plus rollback
- WHEN `scripts/teardown-attendee.sh dan` is run
- THEN both SageMaker endpoints are deleted
- AND all three Lambdas are deleted
- AND the dashboard is deleted
- AND `s3://workshop-lab-dan-audit/` still exists with both audit
  entries intact

### Requirement: Production-vs-Lab Gap Documented
The Session 2 README and the audit_trail module README MUST flag specific
lab simplifications (`shared/terraform-modules/audit_trail/README.md`).

#### Scenario: README contains disclosures
- GIVEN the repo is shipped
- WHEN
  `MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/README.md` is
  read
- THEN it explicitly states this lab's audit configuration is simplified
  for teaching and lists production controls a real deployment would add
  (MFA-delete, object-lock, multi-actor approval gate)
