# AGENTS.md Template

`AGENTS.md` is the per-repo configuration file that tells agents how to behave in a specific repository context. It lives in the repo root and serves as the agent's operating manual for that codebase — what the repo is, what the agent is allowed to do, what's off-limits, and how to escalate when uncertain.

Think of it as the agent equivalent of a `CONTRIBUTING.md`: it sets expectations before work begins.

---

## Template

```markdown
# AGENTS.md

## Repository Context

[What this repo is, what it does, what it does NOT do. Be specific enough that an agent reading this can orient itself without additional context.]

## Agent Behavior Rules

[What agents are allowed to do in this repository. Be explicit — implicit permission is how agent scope creeps.]

## Off-Limits

[Explicit prohibitions. What agents must NOT do, modify, or access in this repo. When in doubt, list it here.]

## CI/CD Context

[Which pipeline runs on this repo, what triggers mean, how to interpret CI results.]

## Escalation

[What the agent should do when it's uncertain. When to stop, who to notify, how to flag.]

## Tool Access

[Which MCP servers or tools are configured for this repo, what they provide, and what they don't.]
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

## Agent Behavior Rules

Agents operating in this repository may:

1. Read any file in the repository to understand context, code structure, and dependencies.
2. Analyze CI/CD failure logs from GitHub Actions and correlate them with recent commits.
3. Recommend code changes by describing the fix in a PR comment or issue. Recommendations must include the file path, the specific change, and the rationale.
4. Query Prometheus metrics (read-only) via the configured MCP server to correlate failures with runtime behavior.
5. Read Terraform plan output to understand infrastructure changes. Never read or reference the state file directly.
6. Run the test suite locally (`npm test` in `services/api/` or `services/web/`) to validate hypotheses about failure causes.

Agents operating in this repository must:

1. Cite the specific files and line numbers that informed their recommendation.
2. Express uncertainty explicitly when a failure could have multiple root causes. "I'm not sure" is a valid and expected output.
3. Respect the `.agentignore` file if present (same syntax as `.gitignore`).

## Off-Limits

Agents must NOT:

1. **Modify files in `infra/`** — Terraform changes require infrastructure review. Agents may read and analyze, but all infrastructure changes go through the platform team.
2. **Access or reference secrets** — No reading `.env` files, AWS credentials, database connection strings, or API keys. If a failure analysis requires knowledge of a secret's value, escalate to a human.
3. **Modify `scripts/`** — Operational scripts (especially database migrations) have destructive potential. Read-only.
4. **Push commits or open PRs directly** — Advisory mode only. The agent recommends, a human commits.
5. **Modify CI/CD workflow files** (`.github/workflows/`) — Pipeline changes require platform team review.
6. **Access production databases or caches** — No RDS or ElastiCache access, even read-only. Use metrics and logs for production investigation.
7. **Interact with third-party APIs** (Stripe, SendGrid, Auth0) — These integrations have rate limits and financial implications. Agent access is not authorized.

## CI/CD Context

**Pipeline:** GitHub Actions, defined in `.github/workflows/`.

**Key workflows:**
- `ci.yml` — Runs on every PR. Lints, type-checks, runs unit and integration tests for changed services. Must pass for merge.
- `deploy-staging.yml` — Triggers on merge to `main`. Deploys to EKS staging cluster via ArgoCD.
- `deploy-production.yml` — Manual trigger only. Requires two approvals. Deploys to EKS production clusters in both regions.

**Interpreting CI results:**
- `lint` job failure → Check ESLint and Prettier output. Usually a formatting issue or unused import. Straightforward to diagnose.
- `typecheck` job failure → TypeScript compilation error. Check the specific file and line in the error output. Often caused by changes in `packages/shared/` that affect downstream services.
- `test-unit` job failure → Unit test failure. Check the test name and the module under test. Look at the most recent commit to that module.
- `test-integration` job failure → May be a code issue or an environment issue (test database, external service mock). Check if the same test passed on the previous commit before assuming a code problem.
- `build` job failure → Usually a dependency issue (missing or conflicting packages) or an esbuild/Vite configuration problem. Check `package-lock.json` changes.

## Escalation

When the agent encounters any of the following, it should stop analysis and flag for human review:

1. **Ambiguous root cause** — If two or more equally plausible explanations exist, present all of them ranked by likelihood and explicitly state that human judgment is needed.
2. **Security-adjacent failures** — Any failure involving authentication, authorization, secrets, or certificate errors. Do not attempt to diagnose; flag immediately.
3. **Infrastructure failures** — EKS node issues, RDS connectivity, networking errors. These require platform team involvement.
4. **Flaky tests** — If the same test has passed and failed on the same code within the last 5 runs, flag it as a flaky test rather than recommending a code fix. Link to the test history.
5. **Failures in `packages/shared/`** — Changes here affect multiple services. Flag for cross-team review rather than recommending a fix in isolation.

Escalation format: Post a comment on the PR or issue with the prefix `[ESCALATION]` followed by a summary of what was found, what's uncertain, and who should look at it (based on CODEOWNERS).

## Tool Access

**Configured MCP servers:**

1. **GitHub MCP Server** — Provides: repository file access, PR and issue management (read), CI workflow status and logs. Does NOT provide: write access to repository contents, workflow dispatch, or admin operations.
2. **Prometheus MCP Server** — Provides: PromQL query execution against the staging Prometheus instance. Does NOT provide: access to production Prometheus, write access (recording rules, alerts), or Alertmanager configuration.
3. **Filesystem MCP Server** — Provides: read access to the local checkout of this repository. Does NOT provide: write access, or access to files outside the repository root.

No other MCP servers or tools are authorized for this repository. If an agent workflow requires a tool not listed here, that's a configuration change that needs platform team review.
```

---

## Writing Your Own AGENTS.md

Start with this example and strip it down to your reality. A few guidelines:

**Be specific about what the repo contains.** Agents use this to scope their analysis. "A microservices repo" is not useful. "A Node.js API in `services/api/` deployed to EKS" is.

**The Off-Limits section is the most important part.** Implicit permission is how scope creeps. If you haven't explicitly prohibited something, an agent (or a future engineer configuring an agent) may assume it's allowed. When in doubt, list it in Off-Limits and remove restrictions later once you have data.

**Keep the CI/CD section grounded in your actual workflow names and job names.** An agent reading "the CI pipeline" can't do anything with that. An agent reading "`ci.yml` runs on every PR with jobs: lint, typecheck, test-unit, test-integration, build" can correlate a failure to the right job immediately.

**Update AGENTS.md when you update your CI/CD pipeline or infrastructure.** Stale agent configuration is as dangerous as stale RBAC policies. Add AGENTS.md review to your pipeline change checklist.
