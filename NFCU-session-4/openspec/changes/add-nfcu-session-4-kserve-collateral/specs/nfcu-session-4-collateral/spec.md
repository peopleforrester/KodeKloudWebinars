# nfcu-session-4-collateral

## ADDED Requirements

### Requirement: NFCU-session-4 directory exists at repo root

The repository SHALL contain a top-level directory `NFCU-session-4/` matching the `NFCU-session-N/` convention used by other sessions in the series.

#### Scenario: Directory follows naming convention
- **GIVEN** a fresh clone of the repository
- **WHEN** the user lists the repo root
- **THEN** `NFCU-session-4/` is present
- **AND** its README documents the per-subdirectory contents

### Requirement: Root README links Session 4

The root `README.md` SHALL list Session 4 under "Available Content" with the session title, date (June 18, 2026), and a one-paragraph description.

> RUN NOTE: deferred to the maintainer. This run is scoped to `NFCU-session-4/` and
> does not edit the repo root. See `RUN_CONFIG.md`.

#### Scenario: Reader finds Session 4 from the repo root
- **GIVEN** a reader on the root README
- **WHEN** they scan "Available Content"
- **THEN** they see a Session 4 entry linking to `NFCU-session-4/README.md`

### Requirement: Per-lab attendee walkthroughs

`attendee-guide/` SHALL contain one markdown walkthrough per lab (1, 2, 3, 4), each with prerequisites, step-by-step instructions, success criteria, and time budget.

#### Scenario: Attendee re-runs a lab post-session
- **GIVEN** an attendee 7 days after the live session
- **WHEN** they open any lab walkthrough
- **THEN** the kubectl commands, expected outputs, and pass criteria are sufficient to complete the lab without the recording

### Requirement: Self-service reproduction path is documented

`attendee-guide/reproduce-on-your-aws-account.md` SHALL document how an attendee reproduces the entire session on their own AWS account using the EKS Terraform module.

#### Scenario: Attendee reproduces without lab platform access
- **GIVEN** an attendee with their own AWS account and Terraform installed
- **WHEN** they follow `reproduce-on-your-aws-account.md`
- **THEN** they end up with a working KServe cluster running labs 1–4
- **AND** the document includes a cost estimate before they apply

### Requirement: Reference card is print-friendly

`reference-card/kserve-on-k8s.md` SHALL summarize KServe primitives, deployment modes, GPU cost levers, and canary vs shadow decision in one printed letter-size page.

#### Scenario: Reference card renders cleanly
- **GIVEN** the reference card markdown
- **WHEN** rendered via pandoc with 0.5-inch margins
- **THEN** the PDF is exactly 1 page with no content cut off
