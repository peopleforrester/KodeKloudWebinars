# KodeKloudWebinars — OpenSpec Project Context

## Purpose

Practitioner collateral from KodeKloud webinars. Each webinar gets a top-level directory containing the slides reference, attendee-facing docs, lab manifests, demo apps, and a definition-of-done checklist for the lab engineering team.

## Stack

- Documentation: Markdown (prose-driven, narrative voice)
- Lab infrastructure: Kubernetes (1.34+), KServe, Knative, kustomize, Helm
- Cluster provisioning: Terraform (AWS / EKS), kind / k3d for local
- Demo apps: Python 3.12+, FastAPI, k6, kubectl
- Container images: built via Docker / nerdctl, published to public ECR
- Cost attribution: Kubecost OSS / OpenCost

## Conventions

- **Per-webinar directory** at repo root using the `NFCU-session-N/` naming convention for the NFCU engagement (the `Agentic_DevOps/` directory predates this convention and stays as-is).
- **Per-concern subdirectories** within each webinar directory (e.g., `manifests/`, `tests/`, `runbook/`, `reference-card/`, `cluster/`).
- **README at every level.** Each directory explains what's in it and how to use it.
- **No code in markdown** beyond illustrative snippets. Runnable code lives in its own files.
- **Prose voice.** Direct. Declarative. No marketing language. No "exciting." No "leverages." Tone reference: `Agentic_DevOps/90-day-playbook/playbook.md`.
- **Time-budgeted.** Anything attendee-facing names the duration upfront.
- **Failure modes explicit.** Every lab has a troubleshooting matrix.

## OpenSpec Workflow

- Changes live in `openspec/changes/<change-id>/`.
- After implementation, archive the change by moving its `specs/` deltas into `openspec/specs/` as the new current state.
- Each capability spec uses EARS-style SHALL requirements with Given/When/Then scenarios.

## Run note (this clone)

For the NFCU engagement in this repository, each session's OpenSpec tree is nested
under its session directory (e.g., `NFCU-session-4/openspec/`) rather than at the
repository root. See `NFCU-session-4/RUN_CONFIG.md` for the path mapping.
