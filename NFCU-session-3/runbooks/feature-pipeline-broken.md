# Runbook: Feature Pipeline Broken

> **Routing rule — read first.**
> **If fixing requires understanding the model → page the model owner.**
> **If fixing uses infrastructure tools → DevOps handles.**

| Field | Value |
|-------|-------|
| Expected alarm/signal | `Drift-PSI-{attendee_id}` (driven by `workclass`) |
| First responder | DevOps (data infrastructure) |
| Severity | Sev2 |

A feature stopped arriving correctly — here, `workclass` is NULL/empty. The model
still returns 200s with normal latency, so only the model-layer metrics catch it.
This is usually a DevOps fix (upstream data infra), and you escalate to the model
owner only if the root cause is a schema change that requires retraining.

## Detection

- `Drift-PSI-{attendee_id}` is in ALARM. On the dashboard's per-feature PSI widget,
  **one** feature (`workclass`) spikes past 0.25 while the others stay below 0.10.
- Infrastructure row looks healthy (invocations normal, latency normal, no 5XX) —
  the tell-tale of a silent data problem.

## Triage

- Inspect recent predictions in the shadow-logs bucket and confirm `workclass` is
  empty/NULL:
  ```bash
  aws s3 ls s3://workshop-lab-{attendee_id}-shadow-logs/predictions/ --recursive | tail
  # sample a recent object and look at the workclass field
  ```
- Check upstream data freshness: when did the feature pipeline last write? Is the
  source table/feed stale?
- Diff against recent deploys: was there a schema change or a column rename in the
  feature pipeline in the last 24h?
- Confirm the spike is isolated to one feature (per-feature PSI), not broad drift.

## Decision

- Apply the routing rule. A NULL field from a broken feed is an **infrastructure**
  problem → **DevOps handles**. Page the **model owner only if** triage shows the
  upstream change is a deliberate schema change that requires the model to be
  retrained against the new feature definition.

## Containment

- Restore the upstream feed or roll back the pipeline change that dropped the
  field. If the bad feed cannot be fixed immediately, fail the affected requests
  loudly (reject NULL `workclass`) rather than scoring on a silently-missing
  feature.

## Resolution

- Confirm `workclass` populates again and `Drift-PSI-{attendee_id}` returns to OK.
- Backfill or discard the window of predictions made on NULL features per data
  policy. File a follow-up to add an input-validation check at ingestion so a
  missing feature fails fast instead of silently degrading predictions.
