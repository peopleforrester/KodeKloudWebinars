# nfcu-session-4-local-cluster

## ADDED Requirements

### Requirement: Local kind cluster supports the full session

`cluster/local/up.sh` SHALL create a kind cluster sufficient to run labs 1–4 (XGBoost + TinyLlama on CPU) on a developer laptop.

#### Scenario: Speaker rehearses on laptop
- **GIVEN** a laptop with Docker, kubectl, helm, kind, and 16 Gi RAM
- **WHEN** the speaker runs `bash cluster/local/up.sh`
- **THEN** within 15 minutes a 3-node kind cluster is ready with all add-ons
- **AND** the same lab manifests apply against it as against the EKS cluster

### Requirement: Local teardown is complete

`cluster/local/down.sh` SHALL destroy the kind cluster and remove related Docker artifacts.

#### Scenario: Clean slate after teardown
- **GIVEN** a kind cluster created by up.sh
- **WHEN** the user runs `bash cluster/local/down.sh`
- **THEN** `kind get clusters` does not list the cluster
- **AND** no related Docker containers or networks remain
