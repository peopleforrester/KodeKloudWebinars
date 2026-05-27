# Spec Delta — incident-simulation

## ADDED Requirements

### Requirement: Five Distinct Incident Scenarios
The system SHALL provide exactly five incident scenarios, each with a distinct
alarm pattern and a documented runbook.

#### Scenario: All five scenarios produce expected alarm patterns
- **GIVEN** an attendee invokes the incident-simulator with scenario parameter N in [1, 5]
- **WHEN** the scenario executes
- **THEN** the alarm pattern matches the runbook for that scenario
- **AND** the scenario auto-cleans up within 15 minutes
- **AND** no scenario leaves persistent state in the attendee's sandbox

### Requirement: Round-Robin Scenario Assignment
The system SHALL assign incident scenarios to attendees in round-robin order
across a cohort of 30, not randomly.

#### Scenario: Even scenario distribution across 30 attendees
- **GIVEN** a cohort of 30 attendees indexed 0–29
- **WHEN** scenarios are assigned by the lab platform
- **THEN** each of the five scenarios is assigned to exactly six attendees
- **AND** no scenario is over- or under-represented by more than zero
