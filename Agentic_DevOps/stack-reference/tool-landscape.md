# Agentic DevOps Tool Landscape

**Point-in-time reference: March 2026.** The landscape is moving fast. Verify release dates and maturity levels before citing any of this in production decisions.

This reference organizes the tooling that matters for agentic DevOps into four layers, from infrastructure you already run to the agent intelligence layer where most of the current investment is happening. The goal is orientation, not recommendation. Your stack choices depend on your existing infrastructure, team skills, and risk tolerance.

---

## Layer 1: Foundation (You Probably Already Have This)

These are the systems agents interact with, not agent-specific tooling. If you don't have these in solid shape, agents will amplify your existing problems rather than solve them.

| Tool | What it is and why it matters for agents |
|------|------------------------------------------|
| **Kubernetes** | The dominant container orchestration platform. Agents that interact with infrastructure will target the Kubernetes API. Your RBAC configuration directly determines agent blast radius. |
| **Docker** | Container runtime and image build tooling. Agents analyzing CI failures need to understand Dockerfiles and image layer caching to diagnose build issues accurately. |
| **Terraform** | Infrastructure as Code with declarative state management. Agents can read Terraform plans to understand infrastructure drift, but write access to state files is a high-risk permission that should be deferred well past any initial pilot. |
| **GitHub Actions** | CI/CD orchestration with YAML-based workflows. The most common pipeline system agents will read from and (eventually) write to. GitHub's fine-grained permission model (per-workflow, per-job) maps well to agent boundary design. |
| **ArgoCD** | GitOps-based continuous delivery for Kubernetes. Declarative by design, which makes it a natural fit for agent-recommended changes — the agent proposes a manifest change, ArgoCD syncs it after human approval. |
| **Prometheus** | Metrics collection and alerting. Agents performing incident triage need PromQL access to correlate failure signals. Read-only access to Prometheus is one of the lowest-risk, highest-value agent permissions. |
| **Grafana** | Visualization and dashboarding for metrics, logs, and traces. Relevant to agents primarily through Grafana's API, which enables programmatic dashboard creation for agent observability. |

---

## Layer 2: Platform Layer (The Infrastructure Agents Run On)

These tools provide the runtime substrate and networking for agentic workloads. They matter because agents are long-running, stateful processes that need service discovery, event-driven scaling, and controlled network access.

| Tool | What it is | Why it matters for agentic workloads |
|------|-----------|--------------------------------------|
| **Kubernetes Gateway API** | The successor to Ingress for routing traffic in Kubernetes. Current standard release: v1.4.0. Kubernetes is retiring Ingress NGINX in 2026 — Gateway API is the migration target. | Provides fine-grained traffic routing that lets you isolate agent traffic from production workloads. Header-based routing enables A/B testing agent versions without separate clusters. |
| **Dapr** | Distributed Application Runtime. CNCF graduated project. Sidecar-based building blocks for pub/sub, state management, service invocation. | Agents need durable state (conversation context, tool call history) and reliable pub/sub for event-driven triggers. Dapr provides both without vendor lock-in. The sidecar pattern means agent code doesn't need to embed these capabilities. |
| **KEDA** | Kubernetes Event-Driven Autoscaling. CNCF graduated. Scales workloads based on event sources (queues, streams, cron). | Agents are bursty — CI failure analysis spikes after deployments, incident triage spikes during outages. KEDA scales agent pods based on queue depth rather than CPU, which matches agent usage patterns better than HPA. |
| **Service Mesh (Istio / Linkerd)** | Sidecar-based network proxy layer providing mTLS, traffic management, and observability. | Enforces network-level isolation for agent workloads. Istio offers more features but higher operational complexity and resource overhead. Linkerd is lighter, simpler, and sufficient for most agent isolation use cases. Choose based on what your team already operates, not on agent-specific requirements. |

---

## Layer 3: Agent Infrastructure (Where Most Teams Need to Build Now)

This layer is where the gap is widest between what exists and what teams need. Most tooling here is less than 18 months old in production form.

### MCP (Model Context Protocol)

The open integration standard (originated at Anthropic, now adopted broadly) that defines how agents connect to external tools and data sources. MCP provides a standardized interface so agents can call APIs, read files, query databases, and interact with infrastructure through a common protocol rather than per-tool custom integrations.

**Governance:** MCP was donated to the Linux Foundation's Agentic AI Foundation (AAIF) in December 2025, co-founded by Anthropic, Block, and OpenAI. This gives the protocol vendor-neutral governance.

**Maturity:** The protocol specification is stable and widely adopted. The June 2025 spec formally defined MCP servers as OAuth 2.1 resource servers with mandatory Resource Indicators (RFC 8707) and PKCE — the security standard is solid and well-specified. The November 2025 spec (version 2025-11-25) further refined security. The spec is sound. The ecosystem does not follow it. **Implementation reality as of March 2026:** 30 CVEs were disclosed across MCP server implementations in a 60-day window, and 38% of 500+ scanned MCP servers completely lack authentication. The Snyk February 2026 research found 13.4% of publicly available agent skills (many distributed as MCP servers) had critical vulnerabilities, with 76 confirmed malicious payloads (source: Snyk State of AI-Assisted Development, Feb 2026). Treat every third-party MCP server as untrusted by default. Vet auth implementation before connecting any MCP server to a production agent. Build or consume only servers you can audit.

### A2A (Agent2Agent Protocol)

Google's open protocol for agent-to-agent communication, launched April 2025 and now under the Linux Foundation. Complements MCP — MCP handles agent-to-tool connections, A2A handles agent-to-agent orchestration. Version 0.3 (July 2025) added gRPC support and signed security cards.

**Maturity:** The broader ecosystem has consolidated around MCP for most use cases. A2A adoption is slower and primarily relevant to multi-agent architectures (Level 3+). You do not need A2A for the [90-day playbook](../90-day-playbook/playbook.md). It's noted here so senior engineers know it exists and can evaluate it when planning multi-agent systems.

### KAgent

A framework for deploying and managing AI agents on Kubernetes. Provides CRDs (Custom Resource Definitions) for defining agent workloads, lifecycle management, and integration with Kubernetes-native tooling.

**Maturity:** Production-ready for single-agent deployments. Multi-agent orchestration features are emerging. KodeKloud offers a dedicated course on KAgent for teams ramping up.

### LangGraph 1.0

Multi-step agent orchestration framework with durable execution and human-in-the-loop as a first-class feature. Supports complex agent workflows with state persistence through failures and interrupts.

**Maturity:** GA. 47M+ PyPI downloads. Production deployments at Uber, LinkedIn, and Klarna (source: LangChain public case studies, 2025). The durable execution model means agent state survives container restarts, which matters for long-running CI analysis tasks. The human-in-the-loop pattern maps directly to the advisory mode described in the [90-day playbook](../90-day-playbook/playbook.md).

### Dapr Agents

Agent orchestration built on the Dapr runtime. Extends the CNCF-graduated Dapr project with agent-specific primitives: workflow definitions, tool registries, and multi-agent communication patterns.

**Maturity:** GA. Dapr v1.17 (released February 27, 2026) is the most agent-relevant Dapr release to date: workflow versioning for safely evolving long-running workflow code without breaking in-flight instances, 41% higher workflow throughput, and two new AI agent framework extensions — `dapr-ext-langgraph` and `dapr-ext-strands` — for durable, observable AI agent workflows. If you're building on Dapr, v1.17+ is the minimum version to target. The sidecar pattern means agent state persists through pod failures without custom checkpointing. Cloud-agnostic by design — runs on any Kubernetes cluster. Best fit for teams already running Dapr or operating in multi-cloud environments.

---

## Layer 4: Agent Intelligence (Building and Running the Models)

The models and platforms that power agent reasoning. This layer changes fastest.

| Tool | Production Capability | Honest Limitation |
|------|----------------------|-------------------|
| **Claude Code (Opus 4.6)** | Extended autonomous task execution (14.5-hour task horizon). Native MCP support for tool integration. Strong at multi-file codebase reasoning and infrastructure-as-code analysis. | Token costs at the Opus tier are significant for high-volume use cases. Long task horizons can mask runaway loops if circuit breakers aren't configured. |
| **GitHub Copilot Coding Agent** | GA since September 2025. Deep integration with GitHub's permission model — inherits repository-level access controls automatically. Assigns itself to issues, opens PRs, runs CI. Note: Claude Opus 4.1 and GPT-5 were deprecated from Copilot on February 17, 2026 — current supported models are Opus 4.6, Sonnet 4.6, and GPT-5.4. | Tightly coupled to GitHub's ecosystem. Limited customization of the agent's planning and tool-use behavior compared to framework-based approaches. |
| **Google Agent Development Kit (ADK)** | Live and available for building custom agents on Google Cloud. Integrates with Vertex AI and Google's model lineup. | Strongest when paired with Google Cloud infrastructure. Cross-cloud deployments require additional integration work. |
| **AWS Bedrock** | Managed service for running foundation models with built-in guardrails, knowledge bases, and agent orchestration. IAM-native access control. | Model selection is more limited than self-hosted options. Agent orchestration features are less flexible than framework-based approaches (LangGraph, Dapr Agents). |
| **OpenAI GPT-5.4** | Launched March 5, 2026. Incorporates and supersedes GPT-5.3-Codex capabilities into a general-purpose model with frontier coding, reasoning, and agentic workflows. | Sandboxed execution limits integration with existing CI/CD pipelines and observability stacks. Leads on SWE-Bench Pro (57.7%) while Claude Opus 4.6 leads on repository-level benchmarks and ARC-AGI-2. |

---

## Observability Tools for Agents (Cross-cutting)

This is non-negotiable infrastructure. Do not increase agent autonomy without agent-specific observability in place. Standard APM is insufficient — you need to track agent reasoning, tool use, and cost alongside traditional metrics.

| Tool | Status | What it provides |
|------|--------|-----------------|
| **Datadog LLM Observability + AI Agent Monitoring** | Both GA. Distinct products. | LLM Observability: end-to-end tracing of LLM calls, prompt/response inspection, cost tracking per invocation. AI Agent Monitoring (separate product): covers multi-step agent workflows, tool call tracing, cost attribution per agent run, interactive agent decision-path graphs, and auto-instrumentation for Anthropic, OpenAI, LangChain, and Bedrock SDKs. LLM Experiments (A/B testing for prompts) in preview. Integrates with existing Datadog APM. |
| **New Relic AI Monitoring** | Expanded February 2026 | LLM performance monitoring, token usage tracking, error analysis. Extended in Feb 2026 to support agent workflow tracing and multi-agent system visibility — tracks cross-agent call chains, not just individual LLM calls. 30% quarter-over-quarter adoption growth. |
| **Grafana AI Observability (Assistant)** | GA since October 2025 | Plugin-based LLM monitoring within Grafana. MCP server monitoring added — can now instrument MCP tool call latency and failure rates natively. Also includes VectorDB performance tracking and 5 pre-built dashboards for AI observability. Natural fit for teams already running the Grafana/Prometheus/Loki stack. |
| **Langfuse** | Open source, actively maintained | Self-hosted LLM observability. Trace visualization, prompt management, eval tracking. Best option for teams that need to keep observability data on-prem or want full control over the telemetry pipeline. |
| **OpenTelemetry GenAI SIG** | Semantic conventions v1.37+ production-usable | Defines semantic conventions for LLM and agent telemetry covering agent spans, metrics, and events. Key attributes: `gen_ai.operation.name`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.provider.name`. Status is technically "Development" not "Stable" but the conventions are production-usable and natively adopted by Datadog, New Relic, and Grafana. Instrument to OTel GenAI SemConv v1.37+ now — this is the recommended default for new agent instrumentation, and it makes your telemetry vendor-portable. |

### Agent-Specific Metrics (Instrument These)

These are not optional. Without them, you are operating an agent blind.

- **Reasoning loop count:** How many internal reasoning steps the agent takes per task. Unbounded loops are your primary runaway risk.
- **Tool call success/failure rate:** Track per-tool, not just in aggregate. A spike in failures for one tool often indicates a permission or configuration change, not an agent problem.
- **Token usage and cost per invocation:** Budget per task type. A CI failure analysis that costs $0.15 is fine. One that costs $15 because the agent entered a reasoning loop is a problem.
- **Human override frequency:** The percentage of agent recommendations that humans reject or modify. This is your leading indicator of governance health. Rising override rates mean the agent's context or capabilities need tuning.
- **Loop/stall detection:** Automated alerting when an agent exceeds expected reasoning steps or time-per-task thresholds. Configure circuit breakers, not just alerts.

---

## The Four Failure Modes

These are the patterns that cause agent pilots to fail or cause incidents. Each is covered briefly here for reference — the [90-day playbook](../90-day-playbook/playbook.md) addresses how to mitigate them in practice.

**1. Hallucination Propagation.** An agent generates a plausible but incorrect recommendation (a code fix that introduces a bug, an incident diagnosis that points to the wrong service). If the human reviewer trusts the agent's confidence signal without verification, the hallucination propagates into production. Mitigation: eval suites that include scenarios where the correct answer is "I'm not sure" (see [eval framework](../eval-framework/eval-suite-starter.md)).

**2. Retry Loops Without Circuit Breakers.** An agent fails at a task, retries, fails again, retries — burning tokens and potentially taking repetitive actions. This is the agentic equivalent of an infinite loop, and it's expensive. Mitigation: define retry budgets in the [permission matrix](../agent-boundary-design/permission-matrix-template.md) and enforce them at the infrastructure level.

**3. State Drift (No Audit Trail).** An agent takes a series of actions but the record of what it did is incomplete or missing. When something goes wrong, you can't reconstruct the sequence. Mitigation: structured logging of every tool call and decision point, retained for a defined period, reviewed on a defined cadence.

**4. Deploying Everywhere on Day One.** The most common organizational failure mode. A successful proof of concept leads to rapid expansion without the governance, observability, or eval infrastructure to support it. Mitigation: the [90-day playbook](../90-day-playbook/playbook.md) is deliberately constrained to one use case, then two. Resist the temptation to accelerate.
