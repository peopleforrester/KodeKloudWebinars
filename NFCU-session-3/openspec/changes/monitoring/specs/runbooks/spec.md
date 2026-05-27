# Spec Delta — runbooks

## ADDED Requirements

### Requirement: Five-Phase Runbook Skeleton
The system SHALL provide a runbook template with exactly five phases in order:
detection, triage, decision, containment, resolution.

#### Scenario: Template phases are present and ordered
- **GIVEN** a reader opens `NFCU-session-3/runbooks/runbook-template.md`
- **WHEN** they scan the document structure
- **THEN** they find five top-level sections in the order: Detection, Triage, Decision, Containment, Resolution

### Requirement: Routing Rule Prominent
The system SHALL state the routing rule at the top of every runbook: *"If fixing
requires understanding the model → page model owner. If fixing uses
infrastructure tools → DevOps handles."*

#### Scenario: Routing rule appears at top of every runbook
- **GIVEN** any of the six runbook files in `NFCU-session-3/runbooks/`
- **WHEN** a reader opens the file
- **THEN** the routing rule appears within the first 30 lines

### Requirement: Concept Drift Time-Compression Disclosure
The system SHALL explicitly disclose, in
`NFCU-session-3/runbooks/concept-drift-confirmed.md`, that the lab time-compresses
concept drift and that real-world response windows are months, not minutes.

#### Scenario: Time-compression note present
- **GIVEN** a reader opens `NFCU-session-3/runbooks/concept-drift-confirmed.md`
- **WHEN** they read the document
- **THEN** they find a clearly-labeled note stating real concept drift manifests over months
- **AND** that the lab compresses this for pedagogical purposes
- **AND** that response timing in the lab is not generalizable to real incidents

### Requirement: No Fabricated Regulatory Claims
Runbook and lab guide content SHALL NOT claim compliance with NCUA, FFIEC, or any
other regulatory framework. Content SHALL NOT refer to NFCU as a "bank".

#### Scenario: Content audit confirms no fabricated regulatory claims
- **GIVEN** a reviewer searches all files under `NFCU-session-3/runbooks/` and `NFCU-session-3/LAB_GUIDE.md`
- **WHEN** they grep for "NCUA", "FFIEC", "compliant", "compliance", or "bank"
- **THEN** any matches are either negative ("does not constitute compliance attestation"), descriptive of principles ("aligned with model risk frameworks"), or absent
- **AND** no claim attests that the lab content itself constitutes compliance with a specific framework
