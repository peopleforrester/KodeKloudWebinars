# Spec Delta — drift-reporting

## ADDED Requirements

### Requirement: Evidently Report Generation
The system SHALL generate a complete Evidently AI drift report on demand, covering
all features and all standard drift metrics.

#### Scenario: Report rendered and accessible
- **GIVEN** an attendee invokes `evidently-runner-{attendee_id}` Lambda manually
- **WHEN** the Lambda completes execution
- **THEN** it uploads an HTML report to the drift-reports S3 bucket
- **AND** returns a signed URL with 1-hour expiry
- **AND** the URL renders a browsable Evidently report in any modern browser
- **AND** the report flags features that have drifted in the current window

### Requirement: Evidently 0.7.x API Compliance
The system SHALL use the Evidently 0.7.x API style and SHALL NOT use the legacy
`column_mapping` argument.

#### Scenario: Code uses Dataset with data_definition
- **GIVEN** a code reviewer inspects `NFCU-session-3/lambdas/evidently-runner/handler.py`
- **WHEN** they search for API usage
- **THEN** they find `Dataset(..., data_definition=...)` and `Report([DataDriftPreset(), DataQualityPreset()])`
- **AND** they find no references to `column_mapping` as a Report constructor argument
