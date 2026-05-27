# Spec Delta — performance-estimation

## ADDED Requirements

### Requirement: Ground-Truth-Free Performance Estimation
The system SHALL estimate model performance on a current production window without
using ground truth labels, using NannyML CBPE for binary classification.

#### Scenario: CBPE produces measurable AUC delta on drifted window
- **GIVEN** the reference window contains clean Session 1/2 prediction traffic
- **AND** the current window contains traffic with injected drift on `hours_per_week`
- **WHEN** an attendee invokes `nannyml-runner-{attendee_id}`
- **THEN** the response JSON contains `estimated_auc_reference`, `estimated_auc_current`, and `delta` fields
- **AND** the absolute value of `delta` is greater than 0.01
