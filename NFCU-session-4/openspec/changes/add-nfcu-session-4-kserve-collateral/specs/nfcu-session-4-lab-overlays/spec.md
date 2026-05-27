# nfcu-session-4-lab-overlays

## ADDED Requirements

### Requirement: Per-attendee namespace isolation via kustomize base

`cluster/lab-overlays/base/` SHALL define a kustomize base producing a Namespace, ResourceQuota (4 vCPU / 8 Gi memory / 10 pods), NetworkPolicy denying cross-namespace traffic, and a ServiceAccount with IRSA annotation placeholder.

#### Scenario: Attendee namespace cannot exhaust shared cluster
- **GIVEN** a per-attendee namespace stamped from the base
- **WHEN** the attendee tries to exceed 4 vCPU, 8 Gi memory, or 10 pods
- **THEN** the API rejects with a ResourceQuota error naming the exceeded quota

#### Scenario: Cross-namespace traffic is blocked
- **GIVEN** two attendee namespaces from the same base
- **WHEN** a pod in namespace A reaches for a service in namespace B
- **THEN** the connection is dropped by NetworkPolicy

### Requirement: Sample overlay documents stamping pattern

`cluster/lab-overlays/overlays/attendee-sample/` SHALL contain a complete sample overlay that the KodeKloud lab platform replicates per attendee.

#### Scenario: Lab platform integration is clear
- **GIVEN** a lab engineer reading the overlays directory
- **WHEN** they read the sample overlay's kustomization.yaml
- **THEN** they understand how to stamp 30 attendee namespaces (e.g., via a templating loop)
