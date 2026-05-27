# Spec Delta — lab-platform

## ADDED Requirements

### Requirement: Lab Readiness Verification
The system SHALL provide a script that verifies pre-session readiness for all 30
attendee sandboxes in parallel and reports per-attendee status.

#### Scenario: Readiness check distinguishes healthy from broken sandboxes
- **GIVEN** 30 attendee sandboxes, some healthy and some with torn-down endpoints
- **WHEN** `NFCU-session-3/scripts/verify-lab-readiness.sh` is invoked
- **THEN** it produces a table with one row per attendee and a green/red status indicator
- **AND** red rows identify the specific failure mode (endpoint missing, alarm misconfigured, dashboard not provisioned, etc.)

### Requirement: Touch Boundary
This change SHALL NOT modify code outside the touch boundary defined in D11.

> **Build note:** the authoritative spec scenario allows
> `.github/workflows/nfcu-session-3-*.yml` at the repo root as the one exception.
> For this build the workflow is nested under `NFCU-session-3/` per the build
> owner's "everything nested" directive, so the effective boundary is
> `NFCU-session-3/**` only. See `../../../../RUN_CONFIG.md`.

#### Scenario: No files modified outside Session 3 scope
- **GIVEN** this change has been fully implemented
- **WHEN** a diff is run against the repository before and after the change
- **THEN** modified paths fall only within `NFCU-session-3/**`
- **AND** no files under `Agentic_DevOps/`, `NFCU-session-1/`, `NFCU-session-2/`, `NFCU-session-4/`, or repo-root `README.md`/`CLAUDE.md`/`.gitignore`/`LICENSE` are modified
