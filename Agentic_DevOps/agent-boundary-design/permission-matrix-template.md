# Agent Permission Matrix

Use this template for every agent before deployment. The matrix defines the agent's blast radius — what it can read, write, execute, and what requires human approval. An agent without a completed permission matrix should not be connected to any system.

Fill this out, commit it to your repo (we recommend alongside your `AGENTS.md`), and review it with your security team before the agent goes live. Schedule a review date no more than 90 days from deployment.

---

## Template

```markdown
# Agent Permission Matrix

## Agent: [Name / Purpose]
## Deployment date:
## Owner (person accountable for this agent):
## Review date (max 90 days from deployment):

---

| Resource | Can READ | Can WRITE | Can EXECUTE | Requires Human Approval |
|----------|----------|-----------|-------------|------------------------|
| Source code repo | | | | |
| CI/CD pipeline config | | | | |
| Container registry | | | | |
| Kubernetes cluster (prod) | | | | |
| Kubernetes cluster (staging) | | | | |
| Infrastructure state (Terraform) | | | | |
| Secrets / credential store | | | | |
| Incident management system | | | | |
| Deployment tooling | | | | |
| Log/metrics store | | | | |

---

## Approval Gates

List every action this agent can take that requires human approval before execution:

1.
2.
3.

## Explicitly Out of Scope

List what this agent is explicitly NOT permitted to do, even if technically possible:

1.
2.
3.

## Retry Budget

- Maximum retries on failure: [number]
- Retry delay: [seconds]
- Circuit breaker behavior: [what happens when budget is exhausted]

## Audit Trail

- Where are agent actions logged: [location]
- Log retention: [duration]
- Who reviews logs and how often: [name/role, cadence]
```

---

## Completed Example: CI Build Failure Analysis Agent

This is the agent described in the [90-day playbook](../90-day-playbook/playbook.md) — the recommended first use case. It operates in advisory mode only: it reads CI failure logs, analyzes root causes, and recommends fixes. It never writes code or modifies infrastructure directly.

```markdown
# Agent Permission Matrix

## Agent: CI Build Failure Analyzer (advisory mode)
## Deployment date: 2026-04-15
## Owner: Jamie Chen, Senior Platform Engineer
## Review date: 2026-07-14

---

| Resource | Can READ | Can WRITE | Can EXECUTE | Requires Human Approval |
|----------|----------|-----------|-------------|------------------------|
| Source code repo | Yes — full repo read access via GitHub App (`contents: read`) | No | No | N/A |
| CI/CD pipeline config | Yes — workflow files and logs (`actions: read`) | No | No | N/A |
| Container registry | Yes — image manifests and tags (`packages: read`) | No | No | N/A |
| Kubernetes cluster (prod) | No | No | No | N/A |
| Kubernetes cluster (staging) | Yes — read-only via `view` ClusterRole | No | No | N/A |
| Infrastructure state (Terraform) | Yes — plan output only (no access to state file or secrets) | No | No | N/A |
| Secrets / credential store | No | No | No | N/A |
| Incident management system | No | No | No | N/A |
| Deployment tooling | No | No | No | N/A |
| Log/metrics store | Yes — Prometheus read via service account, Loki log queries | No | No | N/A |

---

## Approval Gates

Every action this agent takes that requires human approval:

1. Posting a recommended fix as a PR comment (agent drafts the comment, human reviews and approves posting)
2. Opening a GitHub issue for a recurring failure pattern (agent drafts, human creates)
3. Escalating to the on-call engineer for failures the agent cannot diagnose (agent recommends escalation, human initiates)

## Explicitly Out of Scope

What this agent is NOT permitted to do, even if technically possible:

1. Commit code or open pull requests (advisory mode only — it recommends, it does not write)
2. Access production Kubernetes clusters, including read access
3. Read, write, or reference secrets or credentials in any form
4. Modify CI/CD pipeline configuration (workflow files, trigger rules, environment variables)
5. Interact with deployment tooling (ArgoCD, Helm, kubectl apply)
6. Access other repositories beyond the one it is configured for

## Retry Budget

- Maximum retries on failure: 3
- Retry delay: 30 seconds (exponential backoff: 30s, 60s, 120s)
- Circuit breaker behavior: After 3 failed retries, the agent stops analysis for that build failure, logs the failure with full context, and posts a message: "Unable to analyze this failure after 3 attempts. Manual triage required." No further action until a human resets.

## Audit Trail

- Where are agent actions logged: Datadog LLM Observability (traces) + GitHub Actions workflow logs (tool calls) + structured JSON logs in the `agent-audit` S3 bucket
- Log retention: 90 days in Datadog, 1 year in S3
- Who reviews logs and how often: Jamie Chen (agent owner), weekly review of override frequency and failure patterns. Security team quarterly review of permission usage.
```

---

## Notes on Using This Template

**Add rows as needed.** The template covers common resources, but your environment may have others — message queues, feature flag systems, database access, external APIs. Add a row for every system the agent can reach, even if the answer is "No" across the board. Explicit denial is more useful than implicit absence.

**The "Requires Human Approval" column is not the same as "Can WRITE."** An agent might have write access to a system (posting comments, creating issues) but still require human approval before exercising it. Advisory mode means the agent has the technical capability but the process requires human sign-off.

**Review this at the scheduled date, not when something goes wrong.** Permission matrices drift the same way RBAC policies drift — slowly, then suddenly. The 90-day review cycle is a forcing function to catch drift before it becomes an incident.
