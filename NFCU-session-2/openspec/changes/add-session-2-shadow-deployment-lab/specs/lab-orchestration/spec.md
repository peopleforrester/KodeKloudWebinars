# Lab Orchestration Specification

## Purpose
Defines the per-attendee provisioning model, lifecycle, cost guards, and
repo-wide tooling constraints that make the workshop deliverable while
preserving Agentic_DevOps/ isolation.

## Requirements

## ADDED Requirements

### Requirement: Per-Attendee Parameterization
All AWS resource names MUST be parameterized by `attendee_id`.

#### Scenario: Two attendees provisioned
- GIVEN attendees `alice` and `bob` are provisioned
- WHEN their resources are inspected
- THEN alice's Lambda is named `shadow-mirror-alice` and bob's is
  `shadow-mirror-bob`
- AND alice's bucket is `workshop-lab-alice-shadow-logs` and bob's is
  `workshop-lab-bob-shadow-logs`
- AND alice's IAM permissions reference only alice's resources

### Requirement: Idempotent Provisioning
`provision-attendee.sh` MUST be safe to re-run.

#### Scenario: Re-run after partial failure
- GIVEN provisioning for `carol` failed halfway
- WHEN `provision-attendee.sh carol` is run again
- THEN previously-created resources are not duplicated
- AND missing resources are created
- AND the script exits 0 once carol's environment is complete

### Requirement: Resource Tagging
Every AWS resource MUST carry tags `Workshop=Session2`,
`Attendee={attendee_id}`, `CostCenter=KodeKloud-NFCU`,
`AutoTeardown=2026-06-16`.

#### Scenario: Cost report by tag
- GIVEN AWS Cost Explorer is queried for `Workshop=Session2`
- WHEN the report is generated
- THEN every resource appears in the report

### Requirement: Lab 1 Provisioning Timing Budget
The challenger deploy workflow MUST poll for `InService` with a 15-minute
timeout.

#### Scenario: Endpoint InService in 7 minutes
- GIVEN an attendee triggers session-2-deploy-challenger.yml
- WHEN the workflow polls describe-endpoint
- THEN the workflow succeeds within Lab 1's 15-minute budget

### Requirement: Cost Per Active Lab Window
Per-attendee active-lab spend MUST land $1.50–$2.50.

#### Scenario: Post-session cost check
- GIVEN the workshop has completed
- WHEN AWS Cost Explorer is queried filtered to the workshop window
- THEN per-attendee cost is between $1.50 and $2.50 inclusive

### Requirement: Agentic_DevOps Isolation
Tooling, workflows, linters, scanners, and tests added by this change MUST NOT
modify, lint, test, or scan any file under `Agentic_DevOps/**`.

#### Scenario: PR touching only Agentic_DevOps triggers no new CI
- GIVEN a PR touches only `Agentic_DevOps/resources.md`
- WHEN GitHub Actions evaluates triggers
- THEN no workflow added by this change runs against the PR
- AND no new CI check appears that did not exist before this change

#### Scenario: Local validation does not crawl Agentic_DevOps
- GIVEN `scripts/validate-local.sh` is run at the repo root
- WHEN it executes
- THEN no command in the script reads, parses, lints, or modifies any
  file under `Agentic_DevOps/`
- AND `Agentic_DevOps/` mtimes are unchanged after the script finishes

### Requirement: Path-Filter Verification
The CI pipeline MUST include an integration test verifying that Session
2 workflows do not run when only non-Session-2 files change.

#### Scenario: Session 3 README change
- GIVEN a PR touches ONLY
  `MLOps_Deployment_Workshop/Session_3_Monitoring_Drift/README.md`
- WHEN GitHub Actions evaluates triggers
- THEN none of session-2-deploy-challenger.yml,
  session-2-promote-challenger.yml, or session-2-rollback.yml appears in
  the PR's check runs
