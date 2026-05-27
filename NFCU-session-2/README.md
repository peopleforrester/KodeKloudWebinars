# MLOps Deployment Workshop

Runnable lab artifacts for the KodeKloud MLOps Deployment Workshop — a
four-session live series on ML model deployment for DevOps engineers in
regulated financial services.

> This tree is self-contained under `NFCU-session-2/`, which acts as the
> workshop repository root: `openspec/`, `shared/`, `.github/`,
> `MLOps_Deployment_Workshop/`, and the repo-wide tooling all live here.

## Available content

### MLOps_Deployment_Workshop/

A four-session live workshop. Session 2 (Champion-Challenger Shadow
Deployments) is the first runnable lab built in this repository.

| Session | Topic | Date | Status |
|---|---|---|---|
| 1 | Deployment Pipelines | June 2, 2026 | TBD (separate change proposal) |
| 2 | Champion-Challenger Shadow Deployments | June 4, 2026 | In development |
| 3 | Monitoring, Drift, and ML Runbooks | June 16, 2026 | TBD (separate change proposal) |
| 4 | Kubernetes Model Serving | TBD | TBD (separate change proposal) |

Sessions are sequential: Session N's outputs are inputs to Session N+1.

## Prerequisites

- Python 3.12, [`uv`](https://docs.astral.sh/uv/)
- Terraform 1.6+
- An AWS sandbox account (provisioned by KodeKloud during the live session)
- `tflint`, `tfsec`, `checkov`, `kics` for Terraform validation

## Quickstart

```bash
make install              # create the Python 3.12 venv and install dev deps
make validate             # run the full local validation chain
make validate-session-2   # Session 2 checks only
```

Attendees: head to
[`MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/`](MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/)
and follow `LAB_GUIDE.md`.

## Governance

Changes are managed with [OpenSpec](https://github.com/Fission-AI/OpenSpec).
The current change proposal lives at
`openspec/changes/add-session-2-shadow-deployment-lab/`. Validate with:

```bash
openspec validate add-session-2-shadow-deployment-lab --strict
```

## License

- Documentation content: CC BY 4.0
- Code (Lambda handlers, Terraform, scripts): Apache 2.0
