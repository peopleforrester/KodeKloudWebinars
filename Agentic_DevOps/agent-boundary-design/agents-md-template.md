# AGENTS.md Template

`AGENTS.md` is an open standard (originated at OpenAI in August 2025, now under the Linux Foundation's Agentic AI Foundation) that gives coding agents — Codex, Claude Code, GitHub Copilot, Cursor, Jules, Devin, and others — a consistent source of project-specific guidance. It lives in the repo root and serves as the agent's operating manual for that codebase.

**What AGENTS.md is:** Codebase context documentation. It tells coding agents what the repo is, how to build and test it, what coding conventions to follow, and where the landmines are. Think of it as the agent equivalent of a `CONTRIBUTING.md`: it sets expectations before work begins.

**What AGENTS.md is not:** Permissions governance. IAM policies, RBAC manifests, and runtime agent permissions do not belong here — those live in the [permission matrix](permission-matrix-template.md). AGENTS.md is read by coding agents that interact with your source code, not by production ops agents that manage your infrastructure. Do not conflate the two.

**When is AGENTS.md relevant to this webinar's audience?** If your CI build failure analysis agent also needs to understand your repo structure, coding conventions, and architecture to make better recommendations, a well-structured AGENTS.md helps the agent reason about your codebase. That's a legitimate use case. Permissions governance lives in the permission matrix, not here.

**What to explicitly exclude from AGENTS.md:**

- IAM policies or permission grants (wrong artifact — use [permission-matrix-template.md](permission-matrix-template.md))
- Runtime ops agent behavior (AGENTS.md is read by coding agents, not production ops agents)
- Sensitive environment details or credentials of any kind

**Keep it under 150 lines.** Long AGENTS.md files degrade agent performance by burying signal in noise.

---

## Template

```markdown
# AGENTS.md

## Repository Context

[What this repo is, what it does, what it does NOT do. Be specific enough that an agent reading this can orient itself without additional context.]

## Architecture Overview

[Major modules, what lives where, key boundaries between components.]

## Coding Conventions and Style

[Language-specific conventions, formatting rules, naming patterns. Reference linter configs where applicable.]

## Build and Test Commands

[Exact commands, not prose descriptions. What an agent needs to run locally.]

## Off-Limits

[Files or paths the agent should not modify. Be explicit — implicit permission is how scope creeps.]

## Escalation Signals

[Patterns that mean the agent should stop and flag for human review, not guess.]

## Gotchas

[Known footguns, legacy patterns, things that look wrong but are intentional.]
```

---

## Completed Example: Acme Platform Monorepo

This example is for a mid-sized monorepo with a Node.js API service, a React frontend, and Terraform infrastructure. It's realistic enough to use as a starting point — copy it, strip the specifics, fill in yours.

```markdown
# AGENTS.md

## Repository Context

This is the Acme Platform monorepo. It contains:

- `services/api/` — Node.js (Express) REST API. Serves the core product. TypeScript, compiled with esbuild.
- `services/web/` — React frontend. Deployed to CloudFront via S3. Uses Vite for builds.
- `infra/` — Terraform configurations for AWS infrastructure (EKS, RDS, ElastiCache, S3, IAM).
- `packages/shared/` — Shared TypeScript types and utility functions used by both services.
- `scripts/` — Operational scripts (database migrations, data backups, deployment helpers).

This repo does NOT contain: ML model training code, data pipelines, or mobile applications. Those live in separate repositories.

Deployment target: AWS EKS (Kubernetes 1.32) in us-east-1 and eu-west-1.

## Architecture Overview

The API service (`services/api/`) is the backend for the React frontend (`services/web/`). They share types and utility functions via `packages/shared/`. The API talks to RDS (PostgreSQL) and ElastiCache (Redis). Infrastructure is managed by Terraform in `infra/`, deployed via ArgoCD to EKS.

Key boundary: `packages/shared/` is consumed by both services. Changes here affect downstream builds. Treat shared package changes as cross-cutting — they require review from both service owners.

## Coding Conventions and Style

- TypeScript strict mode enabled in both services. No `any` types without a comment explaining why.
- ESLint config at repo root (`.eslintrc.js`). Extends `@typescript-eslint/recommended`. Indentation: 2 spaces.
- Prettier for formatting. Config at `.prettierrc`. Run `npx prettier --check .` before committing.
- Named exports only — no default exports. This keeps imports grep-friendly.
- Error handling: throw typed errors from `packages/shared/errors.ts`. Do not throw plain strings.
- Database queries: use the query builder in `services/api/src/db/`. No raw SQL strings in controllers.

## Build and Test Commands

```bash
# Install dependencies (from repo root)
npm ci

# Lint
npx eslint src/ --ext .ts,.tsx

# Type check
npx tsc --noEmit

# Unit tests (API)
cd services/api && npm test

# Unit tests (Web)
cd services/web && npm test

# Integration tests (requires test database — see scripts/setup-test-db.sh)
cd services/api && npm run test:integration

# Build API
cd services/api && npm run build

# Build Web
cd services/web && npm run build
```

## Off-Limits

- **`infra/`** — Terraform changes require infrastructure review. Read and analyze, but do not modify.
- **`scripts/`** — Operational scripts (especially database migrations) have destructive potential. Read-only.
- **`.github/workflows/`** — Pipeline changes require platform team review.
- **Any file containing or referencing secrets** — No `.env` files, AWS credentials, database connection strings, or API keys. If analysis requires knowledge of a secret's value, stop and escalate.

## Escalation Signals

Stop analysis and flag for human review when you encounter:

1. **Ambiguous root cause** — If two or more equally plausible explanations exist, present all of them ranked by likelihood and explicitly state that human judgment is needed.
2. **Security-adjacent failures** — Any failure involving authentication, authorization, secrets, or certificate errors. Do not attempt to diagnose. Flag immediately.
3. **Infrastructure failures** — EKS node issues, RDS connectivity, networking errors. These require platform team involvement.
4. **Flaky tests** — If the same test has passed and failed on the same code within the last 5 runs, flag as flaky rather than recommending a code fix. Link to the test history.
5. **Changes in `packages/shared/`** — Affects multiple services. Flag for cross-team review rather than recommending a fix in isolation.

## Gotchas

- **`services/api/src/legacy/`** — This directory contains v1 API handlers that are deprecated but still serve traffic for three enterprise customers. They look like dead code. They are not. Do not recommend removing them.
- **`packages/shared/src/dates.ts`** — Uses a custom date parsing function instead of a library. This is intentional — the custom parser handles a legacy date format from the v1 API that no standard library supports. Do not recommend replacing it with dayjs/date-fns.
- **Test database in CI** — Integration tests use a containerized PostgreSQL instance started by `scripts/setup-test-db.sh`. Tests that fail with connection errors are usually a CI environment issue, not a code issue.
- **`services/web/public/config.js`** — Runtime configuration injected at deploy time. The version in the repo is a template with placeholder values. Do not treat placeholder values as bugs.
```

---

## Writing Your Own AGENTS.md

Start with the example above and strip it down to your reality. A few guidelines:

**Be specific about what the repo contains.** Agents use this to scope their analysis. "A microservices repo" is not useful. "A Node.js API in `services/api/` deployed to EKS" is.

**The Gotchas section prevents the most expensive mistakes.** Every codebase has things that look wrong but are intentional. If you don't tell the agent, it will recommend "fixing" them — and a reviewer who trusts the agent may approve the change. Write down the things that trip up new team members. Those are exactly the things that will trip up agents.

**The Off-Limits section is your blast radius control.** If you haven't explicitly prohibited something, an agent (or a future engineer configuring an agent) may assume it's allowed. When in doubt, list it in Off-Limits and remove restrictions later once you have data.

**Keep the Build and Test Commands section copy-pasteable.** Exact commands, not descriptions. An agent reading "run the test suite" can't do anything with that. An agent reading `cd services/api && npm test` can.

**Update AGENTS.md when you update your codebase structure.** Stale agent configuration leads to stale recommendations. Add AGENTS.md review to your PR checklist for structural changes.
