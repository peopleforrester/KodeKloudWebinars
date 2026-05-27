# KodeKloud Webinars

Practitioner collateral from KodeKloud webinars. Designed to be used the week after you watch them, not filed away.

The four **NFCU sessions** below form a sequential, hands-on live-demo series on ML model deployment for DevOps engineers in regulated financial services — each session's outputs feed the next. Every session directory is self-contained and has its own README with role-based starting points.

## Available Content

### [Agentic DevOps](Agentic_DevOps/)

Collateral from **"Beyond Copilots: How Agentic AI is Rewriting the DevOps Playbook"** (April 2026).

Templates, checklists, and a structured 90-day path for running your first agentic AI pilot in a DevOps workflow. Includes:

- A governance-first [90-day playbook](Agentic_DevOps/90-day-playbook/playbook.md) for CI build failure analysis
- A team [readiness assessment](Agentic_DevOps/readiness-assessment/assessment.md) scorecard
- [Agent boundary design](Agentic_DevOps/agent-boundary-design/) templates (AGENTS.md and permission matrix)
- An [eval framework](Agentic_DevOps/eval-framework/eval-suite-starter.md) with 10 starter scenarios
- A [tool landscape reference](Agentic_DevOps/stack-reference/tool-landscape.md) organized by the 4-layer stack
- An annotated [external reading list](Agentic_DevOps/resources.md)

See the [Agentic DevOps README](Agentic_DevOps/) for role-based starting points.

### [NFCU Session 1: ML Deployment Pipelines](NFCU-session-1/)

Runnable collateral from **Session 1 of a four-part live-demo series on ML model deployment for DevOps engineers** (June 2026).

A complete, traceable deployment pipeline built around one question: can you trace any prediction back to its training data in under five minutes? Includes:

- A deterministic [sample-model training script](NFCU-session-1/scripts/train-sample-model.py) and an immutable artifact contract
- A [validation gate](NFCU-session-1/pipeline/validate.py) that rejects mutable references, plus container build/scan/sign and [audit-trail](NFCU-session-1/pipeline/audit-trail.py) tooling
- Reusable [Terraform modules](NFCU-session-1/terraform/) for VPC-isolated, KMS-encrypted SageMaker endpoints across dev/staging/production
- A manually-applied [lab platform sandbox](NFCU-session-1/lab-platform-iac/) (OIDC, IAM, buckets, ECR, KMS)
- Three OIDC-only [GitHub Actions workflows](.github/workflows/) with SHA-pinned third-party actions
- A [lab guide](NFCU-session-1/LAB_GUIDE.md), [FAQ](NFCU-session-1/FAQ.md), and an annotated [reading list](NFCU-session-1/resources.md)

See the [NFCU Session 1 README](NFCU-session-1/README.md) for role-based starting points.

### [NFCU Session 2: Champion-Challenger Shadow Deployments](NFCU-session-2/)

Runnable lab artifacts for **Session 2** (June 4, 2026) — running a challenger model in production shadow alongside the champion, with zero customer impact. Includes:

- A [shadow-mirror Lambda](NFCU-session-2/MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/lambdas/shadow-mirror/) that mirrors live traffic to the challenger and a [comparison Lambda](NFCU-session-2/MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/lambdas/comparison/) that scores agreement
- A traffic generator, CloudWatch dashboard, and a reusable `audit_trail` Terraform module (consumed by Session 3)
- An OpenSpec change proposal as the source of truth, plus unit/integration tests

See the [NFCU Session 2 README](NFCU-session-2/README.md) for the full run guide.

### [NFCU Session 3: Keeping 100+ Models Healthy](NFCU-session-3/)

Collateral and lab environment for **Session 3** (June 16, 2026) — monitoring, drift detection, and observability for deployed models, built to catch the model that returns HTTP 200 while quietly predicting wrong. Includes:

- Five [Lambda functions](NFCU-session-3/lambdas/): PSI drift-detector, drift-simulator, Evidently runner, NannyML runner, and an incident-simulator
- A [CloudWatch dashboard and alarms](NFCU-session-3/monitoring/), per-attendee [Terraform](NFCU-session-3/infra/), and a 5-phase [runbook set](NFCU-session-3/runbooks/)
- Unit + moto-mocked integration tests and dry-run result docs

See the [NFCU Session 3 README](NFCU-session-3/README.md) for the self-contained run guide.

### [NFCU Session 4: Kubernetes-Native ML Serving with KServe](NFCU-session-4/)

Collateral for **Session 4** (June 18, 2026) — moving the same workload off SageMaker onto Kubernetes-native serving with KServe. Runs locally on `kind` with no cloud spend, or on your own EKS via the included Terraform. Includes:

- A scale-to-zero `InferenceService`, a CPU-only LLM, per-model cost attribution, and a canary rollout with rollback
- A [local kind cluster](NFCU-session-4/cluster/) with add-ons, [EKS Terraform](NFCU-session-4/cluster/eks/), and CI
- Four hands-on labs in the [attendee guide](NFCU-session-4/attendee-guide/) plus a full-session rehearsal script

See the [NFCU Session 4 README](NFCU-session-4/README.md) for quickstart and labs.

## Usage

Clone, fork, or download the files you need. The templates include filled examples to show the format — replace the example content with your own infrastructure, tools, and failure patterns.

## License

Documentation content is licensed under [CC BY 4.0](LICENSE). Code snippets within the documentation are licensed under [Apache 2.0](LICENSE).
