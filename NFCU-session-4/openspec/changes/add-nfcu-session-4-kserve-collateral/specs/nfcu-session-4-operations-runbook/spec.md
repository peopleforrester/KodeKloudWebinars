# nfcu-session-4-operations-runbook

## ADDED Requirements

### Requirement: Definition-of-Done has dated gates

`runbook/definition-of-done.md` SHALL contain five gated checklists with explicit calendar dates: Pre-Provisioning (by 2026-06-02), Per-Attendee Provisioning (by 2026-06-06), Pre-Session Validation (by 2026-06-13), Session Day (2026-06-18), Post-Session.

#### Scenario: Lab engineer signs off mechanically
- **GIVEN** a lab engineer working through DoD
- **WHEN** they reach a gate's date
- **THEN** every checkbox is binary (done / not done) with no ambiguity
- **AND** any "not done" item blocks session day

### Requirement: Troubleshooting matrix is exhaustive for known failure modes

`runbook/troubleshooting-matrix.md` SHALL contain at least 12 rows covering: storage initializer failures, Pending pods, 503 cold-start, scale-down stuck, k6 errors, LLM OOMKilled, missing Kubecost data, canary not splitting, rollback not restoring, kind networking, helm release name conflicts, ImagePullBackOff.

#### Scenario: Engineer resolves a known symptom in under 5 minutes
- **GIVEN** an attendee reports a known symptom
- **WHEN** the engineer consults the matrix
- **THEN** they find symptom, likely cause, exact remediation command, and a "how to confirm it worked" step

### Requirement: Day-of-operations timeline covers T-60 to T+30

`runbook/day-of-operations.md` SHALL specify operations from T-60 minutes through T+30 minutes for session start (2026-06-18 10:00 AM ET).

#### Scenario: Lab engineer follows timeline without improvisation
- **GIVEN** the day-of doc at any T-N minute entry
- **WHEN** they read it
- **THEN** they know which command to run, which dashboard to check, which Slack channel to message

### Requirement: Cleanup automation has retention rules

`runbook/cleanup-automation.md` SHALL specify what is destroyed within 30 minutes post-session, what persists 24 hours for catch-up labs, and what is fully decommissioned by 2026-06-20.

#### Scenario: Catch-up labs work for 24 hours
- **GIVEN** an attendee returning 12 hours post-session
- **WHEN** they reconnect
- **THEN** their namespace still has all manifests they applied
- **AND** they can complete labs without re-provisioning

#### Scenario: Cluster is fully gone by June 20
- **GIVEN** the cluster persisted 24 hours post-session
- **WHEN** 48 hours have elapsed
- **THEN** no AWS resources from the session remain billable
- **AND** the cleanup is verifiable from automation logs

### Requirement: Speaker AWS spend is anchored in writing

`runbook/speaker-aws-spend.md` SHALL document expected costs for an 8-hour rehearsal-plus-session window with default Terraform sizing.

#### Scenario: Speaker knows what their AWS bill will be
- **GIVEN** the speaker reads the spend doc before `terraform apply`
- **WHEN** they finish
- **THEN** they have a concrete dollar range and a line-item breakdown (EKS control plane, node hours, NLB, EBS, NAT gateway)

### Requirement: Dry-run checklist precedes session day

`runbook/dry-run-checklist.md` SHALL define the end-to-end validation that must complete by 2026-06-13.

#### Scenario: Dry run catches issues before attendees arrive
- **GIVEN** the dry-run checklist
- **WHEN** the lab engineer executes every step against the provisioned cluster
- **THEN** any failure is logged and triaged against the troubleshooting matrix
- **AND** all blocking issues are resolved before 2026-06-18
