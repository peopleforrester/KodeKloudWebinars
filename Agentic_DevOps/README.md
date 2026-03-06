# Agentic DevOps — Webinar Collateral

This repo contains the practitioner collateral from the KodeKloud webinar **"Beyond Copilots: How Agentic AI is Rewriting the DevOps Playbook"** (April 2026). It exists because the webinar covers concepts that need more than slides to be actionable — templates to fill out, checklists to run through, and a structured path to follow. Everything here is designed to be used the week after you watch it, not filed away.

---

## What's Here

| Folder | What it contains | Who it's for |
|--------|-----------------|--------------|
| [90-day-playbook/](90-day-playbook/) | Step-by-step playbook for running your first agentic AI pilot, plus a printable Day 60 decision gate checklist | Team leads and individual engineers running the pilot |
| [readiness-assessment/](readiness-assessment/) | Team self-assessment scorecard across four dimensions (foundation, platform, agent readiness, organizational readiness) | Team leads assessing whether their team is ready to start |
| [agent-boundary-design/](agent-boundary-design/) | Permission matrix template and AGENTS.md template, both with filled examples | Platform engineers and security reviewers defining agent boundaries |
| [eval-framework/](eval-framework/) | Starter eval suite with 10 complete scenarios for CI build failure analysis | Engineers building and validating agent workflows |
| [stack-reference/](stack-reference/) | Point-in-time tool landscape reference organized by the 4-layer stack | Anyone evaluating tooling or needing a shared vocabulary |
| [resources.md](resources.md) | Annotated external reading list — research, case studies, practitioner resources | Anyone who wants to go deeper on specific topics |

---

## Start Here

**"I'm an individual engineer who wants to start using agents in my workflow."**
Start with the [eval framework](eval-framework/eval-suite-starter.md). Understanding how to test agent behavior is the foundation skill — it's more important than picking the right model or tool. Then read the [AGENTS.md template](agent-boundary-design/agents-md-template.md) to see how agent boundaries are defined in a real codebase. When you're ready to propose a pilot to your team, the [90-day playbook](90-day-playbook/playbook.md) gives you the structure.

**"I'm a team lead trying to assess whether my team is ready."**
Start with the [readiness assessment](readiness-assessment/assessment.md). Run it as a 45-minute team session. The score tells you where you stand; the conversation tells you more. Then review the [permission matrix template](agent-boundary-design/permission-matrix-template.md) to understand what governance looks like in practice. If your team scores 29+ on the assessment, move to the [90-day playbook](90-day-playbook/playbook.md).

**"I'm an engineering leader building a business case for agentic AI adoption."**
Start with [resources.md](resources.md) for the industry data (DORA, Opsera, IDC maturity model). Then read the [90-day playbook](90-day-playbook/playbook.md) — specifically the "What You Will Have Built by Day 90" section — to understand what a realistic first outcome looks like. The [readiness assessment](readiness-assessment/assessment.md) gives you a framework for evaluating which teams are ready to start.

---

## How to Use This Repo

Clone it, fork it, or download the files you need. The content is designed to be adapted to your environment — the templates have filled examples to show you the format, but you should replace the example content with your own infrastructure, tools, and failure patterns.

The files cross-reference each other where relevant. The playbook links to the templates and frameworks it depends on. The templates link back to the playbook for context on when and how to use them. Start with whichever entry point matches your role above and follow the links.
