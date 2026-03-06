# Agentic DevOps Readiness Assessment

This is a team self-assessment scorecard that maps to the 4-layer stack described in the [tool landscape reference](../stack-reference/tool-landscape.md). Run it in a 45-minute team session — not solo, not async. The value comes from the conversation it forces, not the number at the end.

Score each item: **0** (not in place), **1** (partially in place), **2** (solid), **3** (strong and documented).

Be honest. Scoring yourself a 3 on "RBAC configured" because it exists but nobody has reviewed the policies in a year is how agent pilots fail. The assessment is only useful if it reflects reality.

---

## Section 1: Foundation Layer (Your Existing Infrastructure)

This section maps to Layer 1 of the stack reference. These are the systems agents will interact with. Gaps here become agent failure modes.

| # | Item | 0 | 1 | 2 | 3 | Score |
|---|------|---|---|---|---|-------|
| 1.1 | Kubernetes in production with RBAC configured | Not running K8s | K8s in prod, RBAC is default/minimal | RBAC configured per-namespace, reviewed in last 12 months | RBAC documented, reviewed in last 6 months, least-privilege enforced | ___ |
| 1.2 | CI/CD pipeline with automated testing (not just build) | Manual builds or build-only CI | CI runs builds and some unit tests | CI runs unit + integration tests on every PR | Full test suite (unit, integration, e2e) with quality gates that block merges | ___ |
| 1.3 | Observability stack (metrics, logs, traces) — not just uptime monitoring | Basic uptime checks only | Metrics collection (Prometheus or equivalent) in place | Metrics + centralized logging (Loki, ELK, etc.) | Full observability: metrics, logs, and distributed tracing correlated | ___ |
| 1.4 | IaC (Terraform or equivalent) with state management | Infrastructure provisioned manually | Some IaC, state managed locally or inconsistently | IaC for most infrastructure, remote state with locking | All infrastructure defined in code, state managed remotely, drift detection in place | ___ |
| 1.5 | Incident response runbooks that are current and actually used | No runbooks | Runbooks exist but are outdated or unused | Runbooks exist and are referenced during incidents | Runbooks current, used in practice, reviewed/updated quarterly | ___ |
| 1.6 | On-call rotation with documented escalation paths | No on-call rotation | Informal on-call, escalation is ad hoc | Formal rotation, escalation paths documented | Rotation with documented escalation, regular handoff reviews, and post-incident follow-up | ___ |

**Section 1 subtotal: ___ / 18**

---

## Section 2: Platform Readiness

This section maps to Layer 2 of the stack reference. These capabilities determine whether your platform can safely host and isolate agent workloads.

| # | Item | 0 | 1 | 2 | 3 | Score |
|---|------|---|---|---|---|-------|
| 2.1 | Kubernetes Gateway API or service mesh in use | Neither | Ingress controller only | Gateway API or service mesh deployed, basic routing | Gateway API or mesh with traffic policies, mTLS, and network-level isolation | ___ |
| 2.2 | Prometheus/Grafana or equivalent with alerting rules that fire correctly | No alerting | Alerting configured but noisy or unreliable | Alerting rules tuned, low false-positive rate | Alerting integrated with on-call tooling, rules reviewed regularly, SLO-based alerts | ___ |
| 2.3 | Container image scanning in CI pipeline | No image scanning | Scanning runs but results aren't acted on | Scanning in CI, critical/high CVEs block deployment | Scanning with policy enforcement, base image governance, and regular review cadence | ___ |
| 2.4 | RBAC policies documented and reviewed in the last 6 months | No documentation of RBAC policies | Policies documented but not reviewed recently | Documented and reviewed within 12 months | Documented, reviewed within 6 months, with a defined review cadence | ___ |
| 2.5 | Secrets management (not hardcoded, not in env vars in plain text) | Secrets in code or plain-text env vars | External secret store used for some secrets | All secrets in a managed store (Vault, AWS Secrets Manager, etc.) | Managed store with rotation policies, audit logging, and least-privilege access | ___ |

**Section 2 subtotal: ___ / 15**

---

## Section 3: Agent Readiness

This section assesses your team's preparedness to work with agents specifically, not just general AI literacy.

| # | Item | 0 | 1 | 2 | 3 | Score |
|---|------|---|---|---|---|-------|
| 3.1 | Team has read and can explain what MCP (Model Context Protocol) is | Never heard of it | Aware it exists, haven't looked into it | One or more engineers have read the spec and understand the integration model | Team has evaluated MCP servers relevant to their stack and understands the security implications | ___ |
| 3.2 | At least one engineer has built or run a basic agent workflow (locally is fine) | No one has tried | Someone has used a coding assistant (Copilot, Claude) but not built a workflow | One engineer has run an agent workflow (LangGraph, Dapr Agents, etc.) locally | Multiple engineers have built agent workflows and can explain the tool-use loop | ___ |
| 3.3 | Eval/testing discipline exists for current automation (you test your pipelines) | Automation is untested | Some pipeline tests exist | Pipeline changes are tested before deployment | Pipeline testing is standard practice with CI-for-CI patterns | ___ |
| 3.4 | IAM hygiene: principle of least privilege is actually practiced, not just in policy docs | Broad permissions, no regular review | Least privilege as policy, inconsistently enforced | Permissions scoped per-service, reviewed annually | Permissions scoped per-service, reviewed quarterly, with automated drift detection | ___ |
| 3.5 | Your team has had an explicit conversation about where you would NOT deploy an agent | Haven't discussed it | Informal conversation, nothing documented | Team has discussed and identified specific off-limits areas | Off-limits areas documented, with rationale, and shared with adjacent teams | ___ |

**Section 3 subtotal: ___ / 15**

---

## Section 4: Organizational Readiness

Technical readiness without organizational support means your pilot dies at the first status meeting.

| # | Item | 0 | 1 | 2 | 3 | Score |
|---|------|---|---|---|---|-------|
| 4.1 | Engineering leadership is aware of and supportive of an agent pilot | Leadership hasn't been briefed | Leadership aware but no explicit support | Leadership supportive, willing to allocate some time | Leadership actively sponsoring with allocated time and budget | ___ |
| 4.2 | Security team has been briefed (even informally) on agent plans | Security team not informed | Informal mention, no structured discussion | Security team briefed with a written summary of planned agent access | Security team engaged as a partner, reviewing permission design and eval criteria | ___ |
| 4.3 | You have 2-3 engineers who can own an agent pod for 90 days alongside existing work | No available bandwidth | People interested but fully loaded | 2-3 engineers with some bandwidth, informally committed | 2-3 engineers with explicit time allocation and manager support | ___ |
| 4.4 | You have at least one CI failure type that is high-volume, well-understood, and currently handled manually | No clear candidate use case | Some ideas but nothing well-characterized | One candidate identified with volume data | Candidate identified with volume data, estimated manual handling time, and documented triage process | ___ |

**Section 4 subtotal: ___ / 12**

---

## Scoring

**Total score: ___ / 60**

| Score Range | Interpretation | Recommended Action |
|-------------|---------------|-------------------|
| **0–15** | Foundation gaps need addressing first. | Focus on Section 1 items. Agent adoption on a weak foundation creates risk without proportional value. Shore up observability, RBAC, and testing discipline before introducing agents. |
| **16–28** | Solid foundation, agent readiness gaps. | Start with eval discipline and MCP basics (Section 3). Run through the [permission matrix template](../agent-boundary-design/permission-matrix-template.md) as a tabletop exercise to surface governance questions early. |
| **29–42** | Ready to start the 90-day playbook. | Begin with Days 1–30 of the [playbook](../90-day-playbook/playbook.md). Your infrastructure and team are prepared for a controlled pilot. |
| **43–60** | Strong foundation across all sections. | You may be able to compress Days 1–30 of the playbook to 2–3 weeks. Consider starting with a slightly more ambitious use case if your Day 60 decision gate data supports it. |

---

## After Scoring

Three things to do immediately after this session:

1. **Identify your lowest-scoring section.** That section determines your actual readiness, regardless of your total score. A team scoring 45 overall but 3 in Section 3 (Agent Readiness) is not ready to deploy agents — they're ready to start learning about agents.

2. **Pick the three lowest-scoring individual items.** These are your pre-pilot work items. Assign owners and timelines before leaving the room.

3. **Schedule a re-assessment in 30 days.** Track whether the gaps you identified are actually closing. If they aren't, that tells you something about organizational readiness (Section 4) that the scorecard itself can't capture.
