# NFCU Session 1: ML Deployment Pipelines — Webinar Collateral

This folder contains the runnable collateral for **Session 1** of a four-session
live-demo webinar series on ML model deployment for DevOps engineers (Session 1:
June 2, 2026). The series answers one question end to end: **can you trace any
prediction your model made, all the way back to the data it was trained on, in under
five minutes?** Everything here is designed to be cloned and re-run after the webinar,
not filed away.

---

## What's here

| File / folder | What it contains | Who it's for |
|--------|-----------------|--------------|
| [session-outline.md](session-outline.md) | The slide-by-slide presenter outline for the live demo | Anyone watching or re-running the session |
| [LAB_GUIDE.md](LAB_GUIDE.md) | Four-segment hands-on walkthrough to replicate the demo at home | Attendees running it themselves |
| [FAQ.md](FAQ.md) | Nine anticipated questions with concise answers | Anyone evaluating the approach |
| [ENVIRONMENTS.md](ENVIRONMENTS.md) | The dev → staging → production promotion flow, triggers, and gates | Anyone running or testing the pipeline |
| [resources.md](resources.md) | Annotated reading list (regulatory + supply-chain + AI-BOM) | Anyone going deeper |
| [requirements.txt](requirements.txt) | Pinned Python dependencies for the scripts | Anyone running the code |
| [pipeline/](pipeline/) | Validation, container build/scan/sign, and audit-trail tooling | Engineers studying the pipeline |
| [terraform/](terraform/) | Reusable modules + dev/staging/production environment compositions | Engineers studying the IaC |
| [lab-platform-iac/](lab-platform-iac/) | Manually-applied sandbox (network, IAM/OIDC, buckets, ECR, KMS) | Whoever sets up the demo account |
| [scripts/](scripts/) | Deterministic training script for the sample model | Engineers reproducing the artifact |
| [tests/smoke/](tests/smoke/) | Sample payload and known input/output fixture | Engineers verifying the endpoint |
| [docs/](docs/) | One-page reference card, action-pinning guide, cross-session continuity | Presenters and deep readers |

The deploy workflows live at the repository root in
[`.github/workflows/`](../.github/workflows/) (GitHub only reads workflows from there),
prefixed `nfcu-session-1-`.

---

## Start here

**"I'm watching the live demo on June 2."**
Read [session-outline.md](session-outline.md). It mirrors the slide flow so you can
follow along and know what each pipeline stage is demonstrating.

**"I want to run this myself after the webinar."**
Start with [lab-platform-iac/README.md](lab-platform-iac/README.md) to stand up the
sandbox account, then follow [LAB_GUIDE.md](LAB_GUIDE.md) through its four segments.

**"I'm running my own webinar from this material."**
Read [session-outline.md](session-outline.md) for the narrative, then the
[docs/](docs/) folder — the [reference card](docs/reference-card.md),
[security-pinning guide](docs/security-pinning.md), and
[cross-session-continuity notes](docs/cross-session-continuity.md) give you the
talking points and the "why" behind each control.

---

## Required tool versions

These versions are not arbitrary — each pins around a specific compatibility or
supply-chain reason:

- **Terraform `>= 1.14`** (1.15.x recommended): 1.13 reached end-of-life on 2026-04-29.
- **Cosign `>= 3.0`**: v2 is maintenance-only; v3 changed the signing surface.
- **Trivy `>= 0.70.0`**: the 0.69.4/0.69.5/0.69.6 builds were poisoned in the March 2026
  supply-chain compromise; 0.70.0 is the first clean line. See
  [docs/security-pinning.md](docs/security-pinning.md).
- **Python 3.11**: matches the SageMaker XGBoost 1.7-1 serving container.

---

## How to use this folder

Clone or fork the repo and work through the lab guide. The Terraform is meant to be
read and applied in your own AWS sandbox; **nothing here applies itself**, and no
secrets are committed. The pieces cross-reference each other — start at the entry
point that matches your role above and follow the links.
