# Agent Boundary Design

The IAM role an agent assumes is its blast radius. This folder contains the templates to define that boundary before any agent touches a pipeline. Fill these out first, review them with your security team, commit them to your repo, and only then connect the agent to your systems.

- [permission-matrix-template.md](permission-matrix-template.md) — Per-agent permission definition table. Includes a completed example for a CI build failure analysis agent.
- [agents-md-template.md](agents-md-template.md) — Starter `AGENTS.md` file to commit to your repo root. Includes a completed example for a mid-sized monorepo.
