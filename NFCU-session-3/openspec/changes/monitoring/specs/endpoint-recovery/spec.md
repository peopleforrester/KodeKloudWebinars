# Spec Delta — endpoint-recovery

## ADDED Requirements

### Requirement: Pre-Flight Restore Script
The system SHALL provide an idempotent restore script that recreates a missing or
unhealthy Session 1/2 SageMaker endpoint in ≤ 4 minutes wall-clock.

#### Scenario: Restore against a torn-down sandbox completes within budget
- **GIVEN** an attendee's Session 1/2 endpoint has been torn down or is `Failed`
- **WHEN** `NFCU-session-3/scripts/restore-session2-endpoint.sh` is invoked
- **THEN** within 4 minutes a new endpoint with status `InService` exists in the sandbox
- **AND** the endpoint returns valid predictions on a UCI Adult test payload

#### Scenario: Restore against a healthy endpoint is a fast no-op
- **GIVEN** an attendee's Session 1/2 endpoint is already `InService`
- **WHEN** `NFCU-session-3/scripts/restore-session2-endpoint.sh` is invoked
- **THEN** the script exits 0 in under 10 seconds without modifying the endpoint
