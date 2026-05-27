# KodeKloud Webinars

Practitioner collateral from KodeKloud webinars. Designed to be used the week after you watch them, not filed away.

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

See the [NFCU Session 1 README](NFCU-session-1/) for role-based starting points.

## Usage

Clone, fork, or download the files you need. The templates include filled examples to show the format — replace the example content with your own infrastructure, tools, and failure patterns.

## License

Documentation content is licensed under [CC BY 4.0](LICENSE). Code snippets within the documentation are licensed under [Apache 2.0](LICENSE).
