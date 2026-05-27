# Runbook: Data Drift

> **Routing rule — read first.**
> **If fixing requires understanding the model → page the model owner.**
> **If fixing uses infrastructure tools → DevOps handles.**

| Field | Value |
|-------|-------|
| Expected alarm/signal | `Drift-PSI-{attendee_id}` (driven by `hours_per_week`) |
| First responder | Model owner (DevOps assists with containment) |
| Severity | Sev3 |

The input distribution has genuinely shifted (not a broken field) — here,
`hours_per_week` moves up. Whether to recalibrate, retrain, or accept the shift is
a **model decision**, so the model owner is paged; DevOps handles containment.

## Detection

- `Drift-PSI-{attendee_id}` in ALARM. Per-feature PSI shows `hours_per_week`
  crossing 0.25 with a sustained (not spiky) climb.
- Values are still in-range and well-formed (contrast with the broken-pipeline
  case, where a feature goes NULL).

## Triage

- Rank features by PSI severity and compare against feature importance — does the
  drifting feature matter to the model's output?
  ```bash
  # per-feature PSI over the last hour
  aws cloudwatch get-metric-data --region us-east-1 \
    --metric-data-queries file://psi-by-feature-query.json \
    --start-time "$(date -u -d '1 hour ago' +%FT%TZ)" --end-time "$(date -u +%FT%TZ)"
  ```
- Run the Evidently report (evidently-runner) for the full drift breakdown and the
  NannyML estimate (nannyml-runner) to see whether estimated performance is moving.
- Determine whether the shift is a real population change or a transient spike.

## Decision

- Apply the routing rule. Deciding *what to do about* genuine input drift —
  recalibrate thresholds, retrain, or accept — **requires understanding the model**
  → **page the model owner**. DevOps owns containment while that decision is made.

## Containment

- If the drift is degrading output quality now (NannyML estimated AUC dropping),
  the model owner may choose to fall back to a previous model version or a
  conservative default; DevOps executes that rollback.
- Otherwise, increase monitoring frequency and hold while the model owner decides.

## Resolution

- The model owner's chosen remedy (retrain/recalibrate/accept-with-monitoring) is
  applied; confirm PSI and the NannyML estimate stabilize. Record the drift event
  and the decision rationale for the model's monitoring history.
