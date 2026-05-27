# Session 2 Architecture — Shadow Deployment via Lambda Fan-Out

This document describes the three established shadow-deployment patterns, why
this lab uses the Lambda fan-out variant, the data flow, the production
equivalents of the lab's traffic-flip mechanism, and how the
`workshop-approver-bot` GitHub App satisfies the promotion workflow's required
review.

## Shadow-deployment patterns

A shadow (or "dark launch") deployment sends a copy of production traffic to a
challenger model while only the champion's response reaches the caller. The
challenger is evaluated on real traffic shape with zero member impact. There are
three common ways to implement the fan-out.

### (a) SageMaker `ShadowProductionVariants`

Amazon SageMaker has **native** shadow-testing support via
`ShadowProductionVariants` on an endpoint, generally available since re:Invent
2022. You declare a production variant and a shadow variant on the same
endpoint; SageMaker mirrors a configurable percentage of inference requests to
the shadow variant, returns only the production variant's response to the
caller, and captures shadow responses for analysis. Promotion is a native
`update-endpoint` operation.

Strengths: no custom fan-out code, managed traffic mirroring, integrated
metrics. Limitation for this lab: it is SageMaker-specific, and the mirroring
and comparison logic live inside the managed feature rather than in code the
attendee can read.

### (b) Istio mirror / Seldon Core shadow predictor

In a Kubernetes serving stack, traffic mirroring is a routing-layer concern.
Istio's `VirtualService` supports a `mirror` destination that copies requests to
a second service while discarding its response from the caller's path. Seldon
Core exposes the same idea as a first-class **shadow predictor** in a
`SeldonDeployment`, routing a shadow copy alongside the primary predictor.

Strengths: no application code changes; mirroring is declarative in the mesh or
serving graph. Limitation for this lab: it presumes a Kubernetes + service-mesh
environment, which is the subject of Session 4, not Session 2.

### (c) Lambda fan-out (this lab)

A Lambda function sits behind an API Gateway HTTP API and explicitly fans each
request out to two backends: the champion synchronously (its response is
returned to the caller) and the challenger asynchronously (its response is
captured to S3, never reaching the caller). A scheduled comparison Lambda joins
the two responses offline and computes the comparison metrics.

## Why this lab chose fan-out

The fan-out pattern was chosen deliberately — not because SageMaker cannot do
shadow natively (it can; see pattern (a)). The reasons:

1. **Portability** — the same pattern works against a SageMaker endpoint, an ECS
   service, an on-prem Kubernetes deployment, or any HTTP-serving inference
   backend. Attendees take home a pattern that is not tied to one cloud feature.
2. **Pedagogical transparency** — the comparison logic (agreement, latency,
   disparate impact) is explicit Python that attendees can read, modify, and
   reason about. Nothing is hidden inside a managed feature.
3. **Cross-environment teaching** — the fan-out illustrates the *mechanics* of
   shadow deployment (request correlation, async isolation, offline comparison,
   gated promotion) that generalize to the other two patterns.

A fuller treatment of this trade-off — including the explicit acknowledgement
that SageMaker has native shadow support — is in
[`why-lambda-fanout.md`](why-lambda-fanout.md).

## Data flow

```
caller → API Gateway → shadow-mirror Lambda
                              │
                              ├─► champion SageMaker endpoint  ──► response → caller
                              │
                              └─► challenger SageMaker endpoint ──► response → S3 (shadow-logs)
                                                                       │
                                                                       ▼
                                       EventBridge (5-min schedule) → comparison Lambda
                                                                       │
                                                                       ├─► CloudWatch custom metrics
                                                                       └─► S3 (comparison-results)
                                                                                 │
                                                                                 ▼
                                                        session-2-promote-challenger.yml reads latest
                                                                                 │
                                                                                 ▼
                                                        criteria evaluated against promotion-criteria.yaml
                                                                                 │
                                                                                 ├─► fail: workflow refuses to flip
                                                                                 └─► pass: workflow updates shadow-mirror
                                                                                          env vars + writes audit entry
```

Key properties of this flow:

- **Champion synchronous, challenger asynchronous.** The shadow-mirror invokes
  the champion with `invoke_endpoint` and returns only its response. The
  challenger is invoked with `invoke_endpoint_async`, so a slow or failing
  challenger can never affect caller-visible latency or correctness. A failing
  challenger is logged, never raised to the caller.
- **Request correlation.** Every request is assigned a UUID `request_id`. The
  shadow-log entry records the input payload, the champion response, and the
  challenger's async output URI, so the comparison Lambda can join champion and
  challenger outputs on `request_id`.
- **Per-attendee isolation.** Each attendee's shadow-mirror writes only to that
  attendee's buckets and invokes only that attendee's endpoints.

## Traffic-flip mechanism and its production equivalents

The `session-2-promote-challenger` workflow flips traffic by swapping two
environment variables on the `shadow-mirror-{attendee-id}` Lambda:
`CHAMPION_ENDPOINT_ARN` and `CHALLENGER_ENDPOINT_ARN`. This is one reversible
API call and is easy for attendees to inspect — but it is a **lab
simplification**, not a production routing mechanism. The Lambda reads its
endpoints from env vars at invocation, so the swap takes effect for subsequent
requests.

In production, routing state lives in a system designed for it. Equivalents to
the env-var swap include:

| Lab mechanism | Production equivalent |
|---|---|
| Lambda env-var swap | **Weighted DNS records** — shift the weight from the champion to the challenger gradually |
| Lambda env-var swap | **Service-mesh routes** — for example Istio `VirtualService` destination weights |
| Lambda env-var swap | **Feature-flag service** — for example LaunchDarkly, toggling the active model behind a flag |
| Lambda env-var swap | **SageMaker native `update-endpoint`** — promote the shadow variant to the production variant |

The lab's mechanism is illustrative. A real deployment would never store routing
state in a Lambda environment variable.

## `workshop-approver-bot` GitHub App setup

The `session-2-promote-challenger` workflow declares a required review so that
promotion is gated on an explicit approval. During the live session there is no
time for a multi-person review loop, so a `workshop-approver-bot` GitHub App
auto-approves that required review. **This is a stand-in for a calendared,
multi-reviewer human approval** (model owner, model validator, deploying
engineer, risk officer) — see the Lab 4 preamble in
[`../LAB_GUIDE.md`](../LAB_GUIDE.md).

Setup outline:

1. **Register a GitHub App** in the workshop organization named
   `workshop-approver-bot`. Grant it the minimum repository permissions needed
   to submit reviews: read access to pull requests and write access to pull
   request reviews.
2. **Install the App** on the KodeKloudWebinars repository.
3. **Configure the protected environment / required reviewers** used by the
   promotion workflow so that the App is an authorized approver of the gated
   step.
4. **Provision the App's credentials** (App ID and private key) as repository or
   environment secrets consumed by the workflow, so it can mint an installation
   token and submit the approval programmatically when the gate is reached.
5. **Scope it to Session 2 promotion only** — the App approves nothing else.

Because the bot is a teaching stand-in, its very existence is the lesson:
production promotion is a deliberate, auditable, multi-actor decision, and the
audit trail (see [`runbook-rollback.md`](runbook-rollback.md) and the audit-trail
specification) records who approved, against which criteria snapshot, and when.
</content>
