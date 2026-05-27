# Spec Delta — monitoring

## ADDED Requirements

### Requirement: Two-Layer Monitoring Dashboard
The system SHALL provide a single CloudWatch dashboard per attendee showing both
infrastructure-layer metrics and model-layer metrics in separate rows.

#### Scenario: Dashboard renders both layers
- **GIVEN** an attendee has applied the dashboard via `aws cloudwatch put-dashboard`
- **WHEN** the attendee opens the dashboard in the AWS Console
- **THEN** infrastructure widgets (invocations, latency, error rates) populate in the top row
- **AND** ML widgets (per-feature PSI, prediction distribution per class) populate in the bottom row

### Requirement: Three Production Alarms
The system SHALL provision exactly three CloudWatch alarms per attendee, each tied
to an SNS topic visible in the lab dashboard but not configured to page external
systems.

#### Scenario: All three alarms exist post-provisioning
- **GIVEN** an attendee sandbox has completed Terraform provisioning
- **WHEN** `aws cloudwatch describe-alarms --alarm-name-prefix workshop-lab-{attendee_id}` is run
- **THEN** exactly three alarms are returned: `Drift-PSI-{attendee_id}`, `Latency-P95-{attendee_id}`, `ErrorRate-{attendee_id}`
- **AND** each alarm is in `OK` state at provisioning time
