# Runbook: <Incident Name>

> **Routing rule — read first.**
> **If fixing requires understanding the model → page the model owner.**
> **If fixing uses infrastructure tools → DevOps handles.**

| Field | Value |
|-------|-------|
| Expected alarm/signal | `<alarm name or "NannyML estimate">` |
| First responder | `<DevOps / Model owner>` |
| Severity | `<Sev2 / Sev3>` |

Use the five phases below in order. The checks are written so an on-call DevOps
engineer can execute them **without model expertise**; the Decision phase is where
you apply the routing rule and decide whether to involve the model owner.

> Model-risk note: per-feature PSI thresholds here (stable < 0.10, investigate
> 0.10–0.25, significant > 0.25) follow standard model-risk monitoring practice.
> This runbook is an operational procedure, not a regulatory attestation.

## Detection

- What fired? Link the alarm / dashboard widget.
- When did it start? Note T0 from the alarm state-change time.
- Scope: one attendee/model or many?

## Triage

- Concrete, copy-pasteable checks to localize the cause (logs, metrics, recent
  changes). Each check states what a "normal" vs "abnormal" result looks like.

## Decision

- Apply the routing rule. State explicitly: does the fix require understanding the
  model, or is it an infrastructure action? Record who is paged and why.

## Containment

- The immediate action that stops user impact (rollback, scale, disable a path).
  Containment is reversible and does not require root-cause certainty.

## Resolution

- The durable fix, verification that the signal has cleared, and the follow-up
  (post-incident note, backlog item, monitoring gap to close).
