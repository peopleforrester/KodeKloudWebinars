# MLOps Deployment Workshop

A four-session live workshop on ML model deployment for DevOps engineers,
Platform Engineers, SREs, and ML Engineers working in regulated financial
services. Each session is a 2-hour live workshop delivered to 25–30 attendees
via KodeKloud-provisioned AWS sandbox accounts.

## Sessions

| # | Topic | Date | Status |
|---|---|---|---|
| 1 | Deployment Pipelines | June 2, 2026 | TBD — separate change proposal |
| 2 | [Champion-Challenger Shadow Deployments](Session_2_Shadow_Deployment/) | June 4, 2026 | **In development** |
| 3 | Monitoring, Drift, and ML Runbooks | June 16, 2026 | TBD — separate change proposal |
| 4 | Kubernetes Model Serving | TBD | TBD — separate change proposal |

Sessions are sequential — Session N's outputs are inputs to Session N+1. The
Session 1 production endpoint must remain InService through June 4; the
Session 2 promoted champion must remain InService through June 16 for Session 3.

## Region

`us-east-1` for all sessions.

## Conventions

- Sample data is public and synthetic-safe (UCI Adult Census Income). No NFCU
  data, no proprietary models.
- All AWS resources are tagged for cost attribution and auto-teardown.
- All endpoint and bucket names are parameterized by attendee id.
