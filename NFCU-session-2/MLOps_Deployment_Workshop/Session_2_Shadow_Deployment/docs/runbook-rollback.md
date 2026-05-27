# Runbook — Rolling Back a Promotion

This runbook covers when and how to use the `session-2-rollback` workflow to
revert a challenger promotion. Rollback is the exact reverse of the
[promotion](architecture.md) traffic flip: it restores the shadow-mirror
Lambda's endpoint environment variables to their pre-promotion values and writes
an audit entry.

## When to roll back

Roll back when post-promotion telemetry breaches the `rollback_criteria`
thresholds in [`../config/promotion-criteria.yaml`](../config/promotion-criteria.yaml):

| Trigger condition | Default threshold |
|---|---|
| Post-promotion accuracy drop | more than **5%** (`post_promotion_accuracy_drop_pct`) |
| Post-promotion error-rate increase | more than **50%** (`post_promotion_error_rate_increase_pct`) |
| Evaluation window | observed over **60 minutes** (`evaluation_window_minutes`) |

In this lab you trigger the rollback manually to rehearse the mechanism. In
production these thresholds would drive an alert (and, in a later session, an
automated rollback). Note the lab simplification from
[`../LAB_GUIDE.md`](../LAB_GUIDE.md) Lab 2: real default outcomes take 12–24
months, so production rollback decisions lean on proxy signals and operational
error rates rather than a labelled accuracy delta available on lab time.

## How to roll back

1. **Confirm a promotion actually occurred.** A rollback reverts an env-var
   swap; if no non-dry-run promotion completed, there is nothing to revert.
   Check for a `promotion_completed` audit entry under
   `s3://workshop-lab-{attendee-id}-audit/audit/YYYY-MM-DD/`.
2. **Trigger the workflow.** Open the **session-2-rollback** workflow and run it
   via `workflow_dispatch`, supplying your `attendee_id`.
3. **Let it complete.** The workflow runs to completion without further input.

## What the rollback does

- Reverts the shadow-mirror env-var swap: `CHAMPION_ENDPOINT_ARN` is restored to
  its pre-promotion value (the original production endpoint) and
  `CHALLENGER_ENDPOINT_ARN` to the challenger. Subsequent caller requests are
  served by the original champion again.
- Writes a JSON audit entry to
  `s3://workshop-lab-{attendee-id}-audit/audit/YYYY-MM-DD/{event-id}.json` with
  `event_type: "rollback_completed"` and the full audit schema (`timestamp`,
  `actor`, `previous_champion_endpoint_arn`, `new_champion_endpoint_arn`,
  `criteria_snapshot`, `workflow_run_url`, `git_commit_sha`).
- Posts the audit entry path to the workflow run summary.

## How to verify

1. **Audit entry exists.** Confirm an object with
   `event_type: "rollback_completed"` exists in the audit bucket for today's
   date. The entry is written within 30 seconds of the revert.
2. **State is restored.** The entry's `new_champion_endpoint_arn` equals the
   `previous_champion_endpoint_arn` from the preceding `promotion_completed`
   entry. Equivalently, the shadow-mirror Lambda's `CHAMPION_ENDPOINT_ARN` now
   points at the original production endpoint.
3. **Trace the story.** Read the `promotion_completed` and `rollback_completed`
   entries together — they form a complete, traceable record of who promoted,
   against which criteria snapshot, and how the system was returned to its prior
   state.

## Notes

- The audit bucket has S3 versioning enabled and **survives teardown** —
  `scripts/teardown-attendee.sh` deletes the endpoints, Lambdas, and dashboard
  but never the audit bucket or its contents.
- The lab's audit configuration is simplified for teaching. A production
  deployment would add MFA-delete, S3 Object Lock for tamper-evidence, and a
  multi-actor approval gate — see the
  [Session 2 README](../README.md) and the audit_trail module README for the
  full gap list.
</content>
