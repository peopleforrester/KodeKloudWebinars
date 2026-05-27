# nfcu-session-4-cluster-addons

## ADDED Requirements

### Requirement: Add-ons bootstrap is idempotent and ordered

`cluster/addons/bootstrap.sh` SHALL install cert-manager, Knative Serving, Kourier, KServe, kube-prometheus-stack, and OpenCost in dependency order. On EKS it additionally installs the AWS Load Balancer Controller before Kourier.

#### Scenario: Bootstrap completes against a fresh cluster
- **GIVEN** an empty cluster (kind or EKS) with kubectl context set
- **WHEN** the user runs `bash cluster/addons/bootstrap.sh eks` or `bash cluster/addons/bootstrap.sh local`
- **THEN** every component reaches Ready=True
- **AND** the script exits 0

#### Scenario: Re-running is a no-op
- **GIVEN** a cluster where bootstrap has already completed
- **WHEN** the user re-runs the same command
- **THEN** no changes are applied
- **AND** the script exits 0

#### Scenario: Failure points at the failing component
- **GIVEN** a component cannot reach Ready within its timeout
- **WHEN** the timeout fires
- **THEN** the script exits non-zero
- **AND** the error message names the failing component
- **AND** dependent components are not installed

### Requirement: All Helm charts are version-pinned

Every helm values file SHALL include a comment header naming the `chartVersion`, `appVersion`, and upstream chart URL.

#### Scenario: Version drift is detectable
- **GIVEN** any helm values file
- **WHEN** a reviewer reads it
- **THEN** the chart version and app version are stated in the header
- **AND** no version is declared in any other location

### Requirement: Verification script gates lab work

`cluster/addons/verify.sh` SHALL check every component reports Ready=True and exit non-zero if any do not.

#### Scenario: Verify catches a partial install
- **GIVEN** an environment where Kourier is healthy but KServe is not
- **WHEN** the user runs verify.sh
- **THEN** the exit code is non-zero
- **AND** KServe is named as the failing component
