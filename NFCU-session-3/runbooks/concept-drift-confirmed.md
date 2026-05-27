# Runbook: Concept Drift Confirmed

> **Routing rule — read first.**
> **If fixing requires understanding the model → page the model owner.**
> **If fixing uses infrastructure tools → DevOps handles.**

| Field | Value |
|-------|-------|
| Expected alarm/signal | NannyML estimate (`EstimatedAUCDelta`) — not a threshold alarm |
| First responder | Model owner |
| Severity | Sev3 (slow-burn) |

> ## ⚠️ Time-compression note (read before generalizing)
> **Real concept drift manifests over MONTHS, not minutes.** It is confirmed only
> as ground-truth labels slowly return and reveal that the
> feature→target relationship has changed. **This lab compresses that timeline into
> ~15 minutes** for pedagogical purposes by pushing a batch of synthetic
> ground-truth labels with a 20% accuracy drop. **The lab's response timing is NOT
> generalizable to real incidents** — in production you would observe this trend
> over weeks/months and respond on that horizon, not in a 15-minute window.

Inputs look normal and the model still returns 200s, but realized accuracy has
fallen: the relationship the model learned no longer holds. Deciding how to
respond is inherently a **model decision** → page the model owner.

## Detection

- The NannyML estimate (nannyml-runner) shows `estimated_auc_current` dropping
  versus `estimated_auc_reference` (negative `delta`), and once labels return,
  realized accuracy confirms the drop.
- Input drift (PSI) may be mild or absent — that is the signature of *concept*
  drift versus *data* drift.

## Triage

- Run nannyml-runner and record the estimated AUC delta; confirm it is a sustained
  decline, not noise.
- As ground-truth labels arrive, compute realized accuracy on recent predictions
  and compare to the reference period.
- Check for a known external regime change (policy, seasonality, market shift) that
  would explain a changed feature→target relationship.

## Decision

- Apply the routing rule. Concluding that the concept has changed and choosing the
  remedy (retrain on recent data, recalibrate, or temporarily narrow the model's
  scope) **requires understanding the model** → **page the model owner**.

## Containment

- While the model owner decides, the team may revert to a more conservative
  decision policy or a human-in-the-loop review for high-impact predictions. This
  is reversible and buys time; it is not the fix.

## Resolution

- The model owner retrains/recalibrates against recent, correctly-labelled data and
  validates the new model before promotion. Confirm the NannyML estimate and
  realized accuracy recover. Record the regime change and update the monitoring
  baseline so the new normal is the reference going forward.
