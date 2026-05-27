# Spec Delta — drift-detection

## ADDED Requirements

### Requirement: Per-Feature PSI Computation
The system SHALL compute Population Stability Index per feature, not as an
aggregate.

#### Scenario: PSI computed per feature on every scheduled run
- **GIVEN** the drift-detector Lambda is scheduled to run every 2 minutes
- **WHEN** the Lambda executes against recent prediction logs
- **THEN** it emits a `DriftPSI/{feature}` CloudWatch metric for each of the 8 input features
- **AND** aggregate PSI is not computed

### Requirement: Drift Alarm Fires on Threshold Crossing
The system SHALL transition the drift alarm to `ALARM` state when any single
feature's PSI exceeds 0.25.

#### Scenario: Single-feature drift triggers alarm
- **GIVEN** traffic is being sent with a deliberately shifted distribution on the `hours_per_week` feature
- **WHEN** the drift-detector observes PSI > 0.25 on `hours_per_week`
- **THEN** the `Drift-PSI-{attendee_id}` alarm transitions to `ALARM` state
- **AND** the alarm reason identifies `hours_per_week` as the drifting feature
- **AND** other features' PSI remains below 0.1

### Requirement: Lab 2 Timing Budget
The system SHALL detect injected drift and transition the alarm to `ALARM` state
within 5 minutes of the drift simulator beginning to send traffic.

#### Scenario: Drift detection within Lab 2 budget
- **GIVEN** the drift-simulator Lambda is invoked
- **WHEN** drifted traffic begins reaching the endpoint at 10 req/s
- **THEN** PSI on `hours_per_week` crosses 0.25 within 5 minutes
- **AND** the drift alarm transitions to `ALARM` state within the same window
