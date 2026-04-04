# Resources

Curated external reading for practitioners building agentic DevOps workflows. Every entry has a date, a source, and a reason to read it. If something is undated, it's not here — undated content in a space moving this fast is unreliable.

---

## Industry Research and Data

**2025 DORA Report — Accelerate State of DevOps**
Source: DORA / Google Cloud, 2025
The 2025 report introduces findings on how AI-assisted development affects delivery throughput versus stability. The key tension: teams using AI tools showed faster delivery metrics but did not uniformly improve stability. Read this for the data on what AI adoption actually does to your DORA metrics, not what it promises to do.

**Opsera 2026 — AI Impact on Developer Productivity**
Source: Opsera Research, 2026
Quantified findings from production environments: 4.6x increase in PR review time when AI generates the code (reviewers spend longer because AI-generated PRs are larger and require more careful inspection), 48% faster PR creation, and 15–18% more vulnerabilities detected in AI-generated PRs compared to human-written code. Read this before building a business case that assumes AI-generated code reduces review burden — the data shows the opposite.

**Snyk — State of AI-Assisted Development, February 2026**
Source: Snyk, February 2026
Security research on the agent tool ecosystem: 13.4% of publicly available agent skills (many distributed as MCP servers) had critical vulnerabilities, with 76 confirmed malicious payloads identified. Read this before installing any third-party MCP server or agent plugin. The same supply chain risks that apply to npm packages and Docker images apply to agent tools — and the ecosystem is younger, less audited, and moving faster.

**Forrester 2026 — Agentic AI Predictions**
Source: Forrester Research, 2026
Prediction that at least one major enterprise will attribute a significant breach to an agentic AI system operating beyond its intended boundaries by end of 2026. Read this for the risk framing: the question is not whether agents will cause incidents, but whether your governance is ready when they do.

**IDC 2026 — AI Maturity Model for Software Development**
Source: IDC, 2026
Defines five maturity levels for AI in software development, from Level 1 (individual ad-hoc AI tool use, ungoverned) through Level 5 (fully autonomous AI-driven development). Key finding: the majority of organizations are at Level 1. Read this to understand where your team sits and what "Level 2" actually requires in terms of governance, process, and infrastructure. The [90-day playbook](90-day-playbook/playbook.md) is designed to take teams from Level 1 to Level 2.

---

## Production Case Studies and Technical Writeups

**AWS DevOps Agent — Production Eval Framework**
Source: AWS, 2025
Technical writeup of the evaluation framework used for AWS's internal DevOps agent. Documents the four-part eval methodology: evaluations (LLM judges + pass@k metrics), trajectory visualization (OpenTelemetry), fast feedback loops, and production sampling. This is the primary source for the eval approach used in the [eval framework](eval-framework/eval-suite-starter.md).

**Datadog Bits AI SRE Agent — GA Announcement**
Source: Datadog, 2025
Announcement and technical overview of Datadog's production SRE agent, which performs automated incident investigation using Datadog's observability platform. Read this for a production example of an agent operating in read-only investigation mode at scale — the pattern is close to the incident triage use case in the [90-day playbook](90-day-playbook/playbook.md).

**Block/Goose PagerDuty MCP Integration**
Source: Block (formerly Square), 2025
Technical writeup of how Block integrated their Goose AI agent with PagerDuty via MCP for incident response workflows. Covers the MCP server architecture, permission model, and the human-in-the-loop pattern for incident remediation. Read this for a real-world example of MCP used in production incident management.

**Elastic — Self-Healing CI/CD Case Study**
Source: Elastic, 2025
Documents Elastic's implementation of AI-assisted CI failure analysis and remediation. The pattern: build fails, agent analyzes the error, recommends a fix, human approves the commit. This is the closest public case study to the primary use case in the [90-day playbook](90-day-playbook/playbook.md) and the source for the "Elastic pattern" described there.

---

## Standards and Specifications

**MCP Authorization Specification — modelcontextprotocol.io**
Source: Model Context Protocol, 2025
The actual specification for OAuth 2.1 + PKCE implementation in MCP servers. Required reading before any team builds or consumes an MCP server. Defines MCP servers as OAuth Resource Servers with mandatory Resource Indicators (RFC 8707). The spec is sound — the ecosystem implementation quality is the problem (see Snyk research above).

**Linux Foundation Agentic AI Foundation (AAIF) — Announcement**
Source: Linux Foundation, December 2025
The governance body for MCP, AGENTS.md, and Goose, co-founded by Anthropic, OpenAI, and Block, with platinum members including AWS, Google, Microsoft, Bloomberg, and Cloudflare. This is where these standards evolve. Bookmark it so you know when specs change.

**Google Agent2Agent (A2A) Protocol — a2aproject.org**
Source: Google, April 2025 (now under Linux Foundation)
Open protocol for agent-to-agent communication, complementing MCP (agent-to-tool). Version 0.3 (July 2025) added gRPC support and signed security cards. Relevant context for teams planning multi-agent architectures at Level 3+. Not required for the [90-day playbook](90-day-playbook/playbook.md), but senior engineers will ask about it.

---

## Practitioner Perspectives

**Bret Fisher — Agentic DevOps Podcast (agenticdevops.fm)**
Source: agenticdevops.fm, ongoing (launched 2025)
Practitioner-focused podcast covering agentic AI in DevOps contexts. Note: this is practitioner perspective and commentary, not peer-reviewed research. Useful for hearing how working engineers and operators are thinking about agent adoption, what's working, and what's failing in practice. Not a substitute for the research cited above, but a good complement.

---

## KodeKloud Learning Paths

KodeKloud offers courses on several technologies referenced in this collateral, including KAgent, Kubernetes, Terraform, Prometheus, and Grafana. Browse the [KodeKloud course catalog](https://kodekloud.com/courses/) for current listings and learning paths.
