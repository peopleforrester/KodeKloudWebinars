# 90-Day Agentic DevOps Getting Started Playbook

## What This Is

This playbook gets one team through a controlled proof of concept for agentic AI in their DevOps workflow. One use case, one team, advisory mode first. It is a governance-first path — you build the guardrails and measurement infrastructure before you give the agent access to anything.

What this does NOT cover: production write access for agents, multi-agent systems, autonomous remediation, or full pipeline automation. Those are Level 3 capabilities that belong on a roadmap, not in a first pilot. This playbook gets you to Level 2 — AI integrated into specific pipeline stages with human approval gates and documented policies.

## The One Use Case to Start With

Automated CI build failure analysis in advisory mode.

The pattern works like this: a CI build fails. The agent reads the failure logs, correlates them with recent commits, available documentation, and the codebase context. It identifies the likely root cause and recommends a fix. A human reviews the recommendation, decides whether to act on it, and commits the change themselves. The agent never writes code or modifies infrastructure directly.

This is the right starting point for three reasons.

First, it's read-only in most implementations. The agent reads logs, code, and metrics. It produces text output (a recommendation). The blast radius of a wrong recommendation is one engineer's time spent reading it — not a broken deployment, not a production incident. Near-zero blast radius means you can learn from agent behavior without taking real risk.

Second, it's measurable from day one. You can track whether the agent's recommendations are correct by comparing them against what the human actually did. You don't need to build custom evaluation infrastructure to get signal — every recommendation the agent makes is an eval data point, and the human review is the ground truth. Over 30 days, you'll have a dataset that tells you exactly how well the agent understands your codebase and failure patterns.

Third, it's reproducible. The agent connects to your existing CI system (GitHub Actions, GitLab CI, Jenkins, whatever you already run) and reads the logs it already produces. No new infrastructure. No new data pipelines. No vendor integration that takes six weeks to negotiate through procurement. You can start with what you have.

## Days 1–30: Foundation

Three workstreams run in parallel during the first 30 days. All three must be complete before the agent goes live in advisory mode.

### Build Your Eval Suite First

Not after the agent is deployed. Before.

Identify your 10 most common CI failure scenarios. These become your test cases. For each scenario, define the input (the failure log the agent receives), the expected output (what the agent should recommend), and the failure criteria (what the agent should definitely not do). The [eval framework](../eval-framework/eval-suite-starter.md) provides the template and 10 example scenarios to start from.

If you wouldn't deploy code without tests, don't deploy agents without evals. The eval suite serves the same function as a test suite: it defines correct behavior before the code runs, not after. It also gives you a regression detection mechanism — when you change the agent's context or model version, you re-run the eval suite to verify behavior hasn't degraded.

For the evaluation methodology itself, follow the four-part pattern that AWS documented from their DevOps Agent production deployment: evaluations using LLM judges alongside pass@k metrics to measure recommendation accuracy; trajectory visualization through OpenTelemetry to verify the agent's reasoning process, not just its final output; fast feedback loops that run in minutes rather than hours so you can iterate quickly; and production sampling to detect behavioral drift after deployment (source: AWS DevOps Agent production writeup, 2025). The [eval framework](../eval-framework/eval-suite-starter.md) covers each of these in detail.

### Define Permissions Explicitly

Create a separate service principal for the agent. Not your personal credentials. Not a shared service account. A dedicated identity with documented, minimal permissions.

For the CI build failure analysis use case, the agent needs read access to: the source code repository, CI pipeline logs and status, container registry manifests (to check image existence), and your metrics/logging store (Prometheus, Loki, or equivalent). It should have zero write access during the foundation phase. The [permission matrix template](../agent-boundary-design/permission-matrix-template.md) provides the format for documenting this — including a completed example for exactly this use case.

Commit the completed permission matrix to your repository. Then create an `AGENTS.md` file in the repo root that tells the agent what it can do, what's off-limits, and how to escalate when uncertain. The [AGENTS.md template](../agent-boundary-design/agents-md-template.md) provides a starter with a filled-out example for a monorepo environment.

Have your security team review both documents. This review is a conversation, not a gate — you want their input on the permission model before the agent goes live, not a sign-off after the fact.

### Form Your Agentic AI Pod

Two to three engineers. Not a committee. Not "everyone who's interested." A small group with defined ownership.

Assign three explicit responsibilities:

- **Eval suite owner:** Maintains the eval suite, runs it before deployments and on schedule, tracks scores over time, adds new scenarios as new failure patterns appear.
- **Observability owner:** Sets up and maintains the agent observability dashboard (token cost, recommendation accuracy, override frequency, tool call patterns). See the [observability tooling reference](../stack-reference/tool-landscape.md) for options.
- **Governance owner:** Maintains the permission matrix and AGENTS.md, coordinates with the security team, owns the Day 60 decision gate review.

One person can hold two roles if you only have two engineers. No one should hold all three — that's a single point of failure for the entire pilot.

## Days 31–60: Validation

The principle for this phase: generate data, not enthusiasm.

The agent is now live in advisory mode on your CI pipeline. It analyzes build failures and recommends fixes. Humans review every recommendation and decide whether to act on it. No exceptions during this phase — the agent recommends, humans approve. If someone on the team starts merging agent recommendations without review because "the agent is usually right," that's a governance failure. Address it immediately.

### Add Observability Before Adding Anything Else

Before you expand the agent's scope, before you increase its permissions, before you add a second use case — instrument what you already have. Pick one observability platform and deploy it:

- **Datadog LLM Observability** (GA since June 2025) — best fit if you're already a Datadog shop. End-to-end tracing with cost tracking.
- **New Relic AI Monitoring** (expanded February 2026) — extended to support agent workflow tracing, not just individual LLM calls.
- **Grafana AI Observability** (GA since October 2025) — natural fit for teams on the Prometheus/Grafana/Loki stack.
- **Langfuse** (open source) — self-hosted option for teams that need to keep telemetry data on-prem.

See the [tool landscape reference](../stack-reference/tool-landscape.md) for more detail on each. What matters is not which one you choose — it's that you have agent-specific observability running before the Day 60 decision gate.

### Four Metrics to Track

These are the metrics your observability dashboard should show. All four are required for the Day 60 decision gate.

**1. Agent recommendation accuracy.** The percentage of agent recommendations that humans agree with and act on. This is your primary effectiveness metric. Calculate it as: (recommendations accepted without modification) / (total recommendations). Track weekly.

**2. False positive rate.** The percentage of agent recommendations that were wrong — the agent identified an incorrect root cause or recommended a fix that would not have resolved the issue. Track this separately from "recommendations the human modified" — a modified recommendation may have been directionally correct, while a false positive is outright wrong.

**3. Net time saved.** Time saved by the agent's recommendation minus time spent reviewing it. If this number is negative or close to zero, the agent is generating work, not reducing it. Measure this honestly — ask the reviewing engineers to estimate, don't assume. Track weekly averages.

**4. Human override frequency.** The percentage of recommendations that humans reject or significantly modify. This is your leading governance health indicator. A rising override frequency means the agent's context or capabilities need tuning. A stable or declining override frequency means the agent is learning your codebase's patterns effectively (or, more precisely, the context you've provided is sufficient for the failure patterns it encounters).

## Days 60 Decision Gate

This is a binary decision, not a discussion. Before the meeting, gather the data. In the meeting, look at the data. Make the call.

Use the [decision gate checklist](decision-gate-checklist.md) to structure the review.

The decision:

```
≥70% human agreement rate → proceed to Days 61–90
<70% human agreement rate → tune context, improve eval suite, stay in advisory mode
```

If you're below 70%, the fix is almost never "better prompts." It's one of two things:

**Bad context.** The agent doesn't have access to enough information about your specific codebase and environment to make accurate recommendations. Check whether the AGENTS.md is detailed enough, whether the agent has access to the right documentation, and whether the failure scenarios you're targeting include enough context for the agent to reason about them. Adding a paragraph to AGENTS.md about how your test database is configured might matter more than any prompt engineering.

**Wrong use case.** The failure modes you're targeting require architectural knowledge or institutional context that the agent can't reason about from code and logs alone. If your most common CI failures are caused by complex interactions between services that aren't documented anywhere, the agent is being asked to make inferences it doesn't have the information to support. Narrow the scope to failure types the agent can actually diagnose with the context available.

Diagnose before you iterate.

**A note on the 70% threshold:** This is a starting benchmark, not an industry standard. Tune it to your organization's risk tolerance. High-stakes environments (financial services, healthcare, regulated infrastructure) may require 85%+ before proceeding. Low-stakes environments with strong human review practices may find 60% sufficient to justify continuing. The threshold should reflect how much you trust the review process, not just the agent.

## Days 61–90: Controlled Expansion

You've passed the Day 60 gate. The agent is performing well on CI build failure analysis. The team has observability, governance documentation, and a working eval suite. Now add one more use case.

### The Second Use Case: AI-Assisted Incident Triage

The pattern: an incident fires. The agent reads the alert, correlates it with recent deployments, metrics, and logs. It surfaces relevant data and forms hypotheses about the root cause. A human reviews the hypotheses and confirms before any remediation action is taken.

This is still advisory mode. The agent surfaces information and hypotheses. Humans make decisions and take actions. The agent never executes remediation steps, modifies infrastructure, or interacts with production systems beyond read access to metrics and logs.

Apply the same discipline from Days 1–30 to this new use case: build the eval suite first (adapt the [eval framework](../eval-framework/eval-suite-starter.md) for incident scenarios), define permissions explicitly (create a new permission matrix — the incident triage agent may need different read access than the CI analysis agent), and assign ownership within the pod.

### What Is Explicitly Not Yet

These capabilities are out of scope for the first 90 days. This list exists because the temptation to accelerate is real, especially after a successful pilot.

- **Write access to production.** Not yet. The data from advisory mode needs to demonstrate the agent's reliability before write access is on the table.
- **Autonomous remediation.** Not yet. The agent recommends, humans execute. This constraint is the single most important governance control you have.
- **Multi-agent systems.** Not yet. Agent-to-agent delegation introduces coordination complexity that requires infrastructure and governance patterns you haven't built yet.
- **Full pipeline automation.** Not yet. Automating the entire CI/CD pipeline with agents is a Level 3+ capability that depends on the Level 2 foundation you're building now.

### Share What You Learn

Share your pilot results across teams as a story, not a mandate. Document what the agent got right, what it got wrong, what you had to tune in the AGENTS.md, where the context gaps were, and what surprised you. That narrative — honest, specific, grounded in data — builds organizational trust faster than any pilot report or executive summary. Other teams will adopt agents based on what their peers experienced, not what a vendor promised.

## What You Will Have Built by Day 90

A concrete inventory of what exists at the end of this playbook:

- **One agentic workflow in production:** CI build failure analysis, advisory mode, with human approval gates on every recommendation.
- **An eval suite** covering your top 10 failure scenarios with pass/fail tracking and a weekly production sampling cadence.
- **Agent observability dashboards** showing token cost per invocation, recommendation accuracy over time, human override frequency, and tool call success/failure rates.
- **IAM documentation** for agent permissions — a completed permission matrix and AGENTS.md committed to the repository and reviewed by your security team.
- **One incident triage workflow** running in advisory mode with its own eval suite and permission matrix.
- **The data set** to make the case for expanding agent scope — 60+ days of recommendation accuracy data, cost tracking, and governance compliance.

IDC's 2026 research on AI maturity estimates that the majority of organizations are at Level 1: individual engineers using AI tools ad hoc, without governance, documentation, or organizational coordination (source: IDC AI Maturity Model, 2026). By day 90, you are at Level 2: AI integrated into specific pipeline stages, with human approval gates, documented policies, eval-driven deployment, and agent-specific observability. Based on the IDC maturity distribution data, that puts you ahead of roughly 85% of the industry — without a breach, without a failed pilot, and with the data to decide what comes next.

## What Comes Next

Level 3 capabilities are being defined right now by the teams building on the Level 2 foundation you just built. They include: write access to staging environments (with policy-as-code guardrails enforcing what the agent can modify and under what conditions), agent-to-agent delegation (one agent identifying a problem and routing it to a specialized agent for resolution), and policy-as-code governance (replacing human approval gates with automated policy checks for well-understood, low-risk actions).

The teams who define what Level 3 looks like are building it now, on top of the Level 2 foundation you just built.
