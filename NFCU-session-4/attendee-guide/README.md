# Attendee Guide

Everything you need to work the four labs — during the session and again the week after.
Each lab is timed and self-contained: the commands, expected output, and pass criteria are
all here, so you don't need the recording to repeat a lab.

## The through-line

Sessions 1–3 deployed this workload on SageMaker. Session 4 asks: what changes when the
serving layer is Kubernetes-native? You deploy a model as an `InferenceService`, watch it
scale on concurrency (and to zero), put a small LLM behind the same API, attribute cost per
model, and ship a new version with a canary you can roll back in one command.

## Order and timing (120 minutes)

| When | Lab | Doc |
|---|---|---|
| T+0 | Setup & prerequisites | [`prerequisites.md`](prerequisites.md) |
| T+12 | Lab 1 — Deploy an InferenceService (12 min) | [`lab-1-deploy-inferenceservice.md`](lab-1-deploy-inferenceservice.md) |
| T+24 | Lab 2 — Load test & autoscaling (12 min) | [`lab-2-load-test-and-scaling.md`](lab-2-load-test-and-scaling.md) |
| T+36 | Lab 3 — An LLM & its cost (15 min) | [`lab-3-llm-and-costs.md`](lab-3-llm-and-costs.md) |
| T+51 | Lab 4 — Canary rollout & rollback (15 min) | [`lab-4-canary-rollout.md`](lab-4-canary-rollout.md) |

The rest of the time is discussion, Q&A, and buffer.

## After the session

- [`reproduce-on-your-aws-account.md`](reproduce-on-your-aws-account.md) — rebuild the
  whole thing on your own AWS account (cost-anchored).
- [`post-session-monday-actions.md`](post-session-monday-actions.md) — the three things to
  do Monday morning.
- [`faq.md`](faq.md) — the questions that come up every time.

## If something breaks

Your lab engineer has the [`troubleshooting matrix`](../runbook/troubleshooting-matrix.md).
Most issues during the labs are cold-start timeouts (wait and retry) or a missing
`storageUri` substitution (see Lab 1).
