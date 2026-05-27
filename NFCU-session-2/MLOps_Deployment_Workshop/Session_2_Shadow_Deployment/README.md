# Session 2 — Shadow Deployment Lab

Champion-challenger shadow deployment for the NFCU MLOps Workshop. You evaluate
a challenger model against the production champion on real-shaped traffic using a
Lambda fan-out pattern that preserves **zero member impact** — the challenger
never affects a caller-visible response.

## Quickstart for attendees

### Prerequisites

- An assigned AWS sandbox account and an `{attendee-id}` (for example, `dan`).
- Python 3.12.
- Terraform 1.6 or newer.
- Repository cloned locally; work inside this Session 2 directory.

### Provision your lab

Provision your per-attendee resources with:

```bash
scripts/provision-attendee.sh {attendee-id}
```

This runs `terraform apply` for your attendee and returns your API Gateway URL
and CloudWatch dashboard URL. It is idempotent and safe to re-run. Provisioning
creates, per attendee:

- The challenger SageMaker endpoint `workshop-lab-{attendee-id}-challenger`
  (the champion `workshop-lab-{attendee-id}-production` is provisioned ahead of
  the session).
- Three Lambdas: `shadow-mirror-{attendee-id}`, `comparison-{attendee-id}`,
  `traffic-generator-{attendee-id}`.
- Two buckets: `workshop-lab-{attendee-id}-shadow-logs`,
  `workshop-lab-{attendee-id}-comparison-results`, plus the audit bucket
  `workshop-lab-{attendee-id}-audit`.
- The CloudWatch dashboard `workshop-lab-{attendee-id}-shadow` (metrics namespace
  `Workshop/Session2`).
- An EventBridge 5-minute schedule driving the comparison Lambda.

### Start the labs

Follow [`LAB_GUIDE.md`](LAB_GUIDE.md). The four labs run 60 minutes total:

1. **Lab 1 (15 min)** — deploy the challenger endpoint.
2. **Lab 2 (12 min)** — generate shadow traffic and inspect the comparison.
3. **Lab 3 (18 min)** — evaluate promotion criteria and run the gate.
4. **Lab 4 (15 min)** — rollback rehearsal and the promotion/audit story.

Supporting documentation under [`docs/`](docs/):

- [`docs/architecture.md`](docs/architecture.md) — the three shadow-deployment
  patterns, why this lab uses Lambda fan-out, the data flow, production
  equivalents of the traffic flip, and the `workshop-approver-bot` setup.
- [`docs/runbook-rollback.md`](docs/runbook-rollback.md) — when and how to use
  the `session-2-rollback` workflow.
- [`docs/why-lambda-fanout.md`](docs/why-lambda-fanout.md) — the pedagogical
  rationale for fan-out over native SageMaker shadow.

The promotion thresholds live in
[`config/promotion-criteria.yaml`](config/promotion-criteria.yaml); the models
are documented in [`models/README.md`](models/README.md). The challenger agrees
with the champion on roughly **92.8%** (0.928) of the UCI Adult test split.

## Production vs lab gaps

This lab is built for teaching, and several aspects are deliberately simplified
relative to a regulated production deployment. The most important gaps:

**Audit configuration is simplified.** This lab's audit bucket has S3 versioning
enabled and survives teardown, but its audit configuration is **simplified for
teaching**. A real deployment would add:

- **MFA-delete on the audit bucket** — so that deleting audit objects or
  versions requires a multi-factor authentication step, preventing casual or
  compromised-credential deletion of the audit trail.
- **S3 Object Lock for tamper-evidence** — write-once-read-many retention so
  audit entries cannot be altered or deleted within their retention window,
  giving a tamper-evident record.
- **A multi-actor approval gate** — promotion approval as a calendared event
  with the model owner, model validator, deploying engineer, and risk officer
  each signing off. In this lab the `workshop-approver-bot` GitHub App
  auto-approves the promotion review as a **stand-in** for that human loop.

The same disclosures appear in the `shared/terraform-modules/audit_trail/`
module README.

**Other lab simplifications** (detailed in [`LAB_GUIDE.md`](LAB_GUIDE.md) and
[`docs/architecture.md`](docs/architecture.md)):

- The traffic flip is a Lambda env-var swap, standing in for weighted DNS,
  service-mesh routes, feature flags, or SageMaker `update-endpoint`.
- Protected-class fields (`sex`, `race`) from UCI Adult are binary/coarse and
  not representative of production fair-lending analysis.
- Ground-truth labels are available immediately; in real credit modeling default
  outcomes take 12–24 months and proxy signals carry the load.
</content>
