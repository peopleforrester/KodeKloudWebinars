# Session 2 Lab Guide — Champion-Challenger Shadow Deployment

This guide walks you through four labs (60 minutes total). You evaluate a
challenger model against the production champion using a shadow-deployment
pattern that preserves **zero member impact** — the challenger never affects a
caller-visible response.

Throughout this guide, `{attendee-id}` is the identifier you were assigned at
the start of the session (for example, `dan`). Substitute it wherever it
appears.

Architecture, the rollback runbook, and the rationale for the Lambda fan-out
pattern live under [`docs/`](docs/). Read [`docs/architecture.md`](docs/architecture.md)
if you want the full data-flow picture before you start.

| Lab | Theme | Time |
|---|---|---|
| Lab 1 | Deploy the challenger endpoint | 15 min |
| Lab 2 | Generate shadow traffic and inspect the comparison | 12 min |
| Lab 3 | Evaluate promotion criteria and run the gate | 18 min |
| Lab 4 | Rollback rehearsal and the promotion/audit story | 15 min |

---

## Lab 1 — Deploy the Challenger Endpoint (15 min)

### Starting State

- Your attendee sandbox is provisioned: the champion endpoint
  `workshop-lab-{attendee-id}-production` is already `InService`, the three
  Lambdas (`shadow-mirror-{attendee-id}`, `comparison-{attendee-id}`,
  `traffic-generator-{attendee-id}`) exist, and the
  `workshop-lab-{attendee-id}-shadow-logs` and
  `workshop-lab-{attendee-id}-comparison-results` buckets are empty.
- The challenger model artifact (`model-v1.0.1`) has been packaged and uploaded.
- The challenger endpoint `workshop-lab-{attendee-id}-challenger` does **not**
  yet exist.

### Objective

Deploy the challenger SageMaker endpoint via the `session-2-deploy-challenger`
workflow and confirm it reaches `InService` within the 15-minute poll budget.

### Steps

1. Open the GitHub Actions tab and select the **session-2-deploy-challenger**
   workflow.
2. Click **Run workflow** (`workflow_dispatch`), enter your `attendee_id`, and
   start the run.
3. The workflow runs `terraform apply` for the challenger endpoint, then polls
   `describe-endpoint`. Endpoint creation typically takes 6–10 minutes; the
   workflow allows up to **15 minutes** before timing out.
4. Watch the workflow log until you see the endpoint status transition to
   `InService`.
5. Confirm the challenger endpoint ARN is written to the workflow run summary.

### Success Criterion

The workflow completes successfully and the run summary shows
`workshop-lab-{attendee-id}-challenger` with status `InService`. Both the
champion and the challenger are now `InService`.

### Troubleshooting

- **Workflow still polling near the 15-minute mark:** SageMaker endpoint
  creation is occasionally slow under account load. If the poll times out,
  re-run the workflow — `terraform apply` is idempotent and will pick up the
  in-flight endpoint rather than recreate it.
- **`terraform apply` fails on quota:** the account may be at its endpoint
  quota. Notify the lab engineer; do not create endpoints manually.
- **Workflow did not trigger from a push:** this workflow is path-filtered to
  the Session 2 directory. Use the manual **Run workflow** button
  (`workflow_dispatch`) instead.

---

## Lab 2 — Generate Shadow Traffic and Inspect the Comparison (12 min)

> **Before you start — protected-class fields are coarse.** The disparate-impact
> comparison in this lab uses two protected-class fields from the UCI Adult
> dataset: `sex` (binary: `Male`/`Female`) and `race` (five coarse categories).
> Real-world fair-lending analysis works with far richer demographic features
> and more nuanced subgroup definitions. **The specific disparate-impact numbers
> you see here are not representative of production fair-lending analysis.** They
> exist only to demonstrate the comparison mechanics.

### Starting State

- Both endpoints are `InService` (from Lab 1).
- The shadow-logs and comparison-results buckets are empty.
- The `comparison-{attendee-id}` Lambda runs automatically every 5 minutes on
  an EventBridge schedule, but has nothing to compare yet.

### Objective

Drive synthetic traffic through the shadow-mirror, let the comparison Lambda
join champion and challenger responses, and inspect the agreement rate, latency
delta, and per-group disparate-impact ratios.

### Steps

1. Invoke the `traffic-generator-{attendee-id}` Lambda manually with a payload
   such as `{"duration_minutes": 5, "rate": 5}`. It reads the UCI Adult test
   split and biases ~15% of samples toward the pre-identified
   champion/challenger disagreement region.
2. Each request flows through the shadow-mirror: the champion is invoked
   synchronously (its response goes back to the generator), and the challenger
   is invoked asynchronously (its output lands in S3). A shadow-log entry is
   written under `s3://workshop-lab-{attendee-id}-shadow-logs/raw/`.
3. Wait for the next 5-minute comparison cycle (or note that challenger async
   outputs may lag the champion by a short interval — see Troubleshooting).
4. Read `s3://workshop-lab-{attendee-id}-comparison-results/latest.json`.
   Inspect the `metrics` block: `agreement_rate`,
   `latency_p95_champion_ms`, `latency_p95_challenger_ms`,
   `latency_p95_delta_pct`, and the `disparate_impact` ratios per
   `sex|race` group.
5. Open the `workshop-lab-{attendee-id}-shadow` CloudWatch dashboard and locate
   the `ShadowAgreementRate`, `ShadowLatencyP95Delta`, and
   `ShadowDisparateImpactRatio` metrics in the `Workshop/Session2` namespace.

### Success Criterion

`latest.json` exists and reports an `agreement_rate` near **0.928** (the
challenger agrees with the champion on roughly 92.8% of the UCI Adult test
split), with non-empty per-group disparate-impact ratios and a populated
`n_observations` count.

### Troubleshooting

- **`latest.json` not present yet:** the comparison Lambda runs on a 5-minute
  schedule. Wait for the next cycle, or invoke the comparison Lambda manually to
  force a pass.
- **`agreement_rate` is 0 or `n_observations` is low:** the challenger's async
  outputs have not landed in S3 yet, so requests are deferred. Check
  `deferred_request_ids` in `latest.json`; wait one more cycle for the async
  outputs to arrive, then re-read.
- **Disparate-impact ratios all 1.0:** too few observations per protected group
  to differentiate. Run the traffic generator longer or at a higher rate.

> **Debrief — ground truth does not arrive on lab time.** UCI Adult ships
> ground-truth labels, so you can compute an accuracy delta immediately. **In
> real credit modeling, default outcomes take 12–24 months to materialize.** A
> production shadow run cannot wait that long for a verdict, so proxy signals —
> agreement rate, prediction-distribution stability, downstream operational
> metrics — do most of the heavy lifting. This lab cannot reproduce that delay;
> keep it in mind when you take the pattern home.

---

## Lab 3 — Evaluate Promotion Criteria and Run the Gate (18 min)

### Starting State

- `latest.json` exists with a populated `metrics` block (from Lab 2).
- The shadow-mirror Lambda's `CHAMPION_ENDPOINT_ARN` points at the production
  endpoint and `CHALLENGER_ENDPOINT_ARN` at the challenger.
- The promotion thresholds in
  [`config/promotion-criteria.yaml`](config/promotion-criteria.yaml) are at
  their shipped defaults (agreement 0.85–0.99, challenger p95 ≤ 200 ms, p95
  delta ≤ 20%, disparate-impact ratio ≥ 0.80, ≥ 1000 observations, ≥ 100 per
  protected group).

### Objective

Run the promotion gate first as a dry run, then for real, and observe that the
gate flips traffic only when **every** criterion passes.

### Steps

1. Open the **session-2-promote-challenger** workflow. Run it with your
   `attendee_id` and **`dry_run: true`**.
2. Read the workflow output. The gate evaluates the latest comparison result
   against `promotion-criteria.yaml`. A passing dry run reports *"criteria met,
   promotion approved (dry run, no changes made)"* and modifies nothing.
3. If the gate reports `not_ready`, read the named failure reasons — for example
   insufficient observations or an out-of-band agreement rate. Return to Lab 2,
   generate more traffic, and re-run the dry run until it passes.
4. Once the dry run passes, run the workflow again with **`dry_run: false`**.
   The promotion review is auto-approved by the `workshop-approver-bot` (see the
   Lab 4 preamble for what this stands in for).
5. On success the workflow swaps `CHAMPION_ENDPOINT_ARN` and
   `CHALLENGER_ENDPOINT_ARN` on the shadow-mirror Lambda and writes a
   `promotion_completed` audit entry to
   `s3://workshop-lab-{attendee-id}-audit/audit/YYYY-MM-DD/{event-id}.json`.
6. Confirm the workflow summary posts the audit entry path.

### Success Criterion

A non-dry-run promotion completes, the shadow-mirror Lambda's
`CHAMPION_ENDPOINT_ARN` now points at the former challenger, and an audit entry
with `event_type: "promotion_completed"` exists in your audit bucket containing
`previous_champion_endpoint_arn`, `new_champion_endpoint_arn`,
`criteria_snapshot`, `workflow_run_url`, and `git_commit_sha`.

### Troubleshooting

- **Gate refuses with "criteria not met":** this is correct behavior when a
  criterion fails. The message names the failing criterion with actual vs.
  required values. No Lambda env var is modified on a failure.
- **Agreement too high (above 0.99):** the gate refuses — a challenger that
  agrees with the champion ~99.5% of the time may not be meaningfully different.
  This is an intentional guardrail, not a bug.
- **Agreement too low (below 0.85):** the gate refuses — too much disagreement
  to trust the challenger. Confirm your traffic run used the default generator
  settings.
- **"500 observations, minimum 1000 required":** run the traffic generator
  longer (increase `duration_minutes` or `rate`) so the comparison window
  accumulates enough observations.

---

## Lab 4 — Rollback Rehearsal and the Promotion/Audit Story (15 min)

> **Before you start — the auto-approval bot is a stand-in.** The promotion
> workflow's required review is auto-approved by a `workshop-approver-bot`
> GitHub App so the live session stays on schedule. **In production this is a
> calendared event with the model owner, model validator, deploying engineer,
> and risk officer all signing off.** The auto-approval bot in this lab is a
> stand-in for that multi-reviewer human loop — never a model for production.

> **Before you start — the env-var swap is a lab simplification.** This lab
> "flips traffic" by swapping two environment variables
> (`CHAMPION_ENDPOINT_ARN` and `CHALLENGER_ENDPOINT_ARN`) on the shadow-mirror
> Lambda. That is pedagogically clean and one reversible API call, but it is a
> **lab simplification of the real traffic flip.** Production routing uses
> weighted DNS records, service-mesh routes (for example Istio VirtualService
> weights), feature-flag services, or SageMaker's native `update-endpoint`. See
> [`docs/architecture.md`](docs/architecture.md) for the production equivalents.

### Starting State

- A promotion has completed (from Lab 3): the former challenger is now the
  champion, and a `promotion_completed` audit entry exists.
- The shadow-mirror Lambda's env vars reflect the swapped state.

### Objective

Rehearse a rollback using the `session-2-rollback` workflow and trace the full
promotion → rollback story through the audit trail.

### Steps

1. Review the `rollback_criteria` block in `promotion-criteria.yaml`: a
   post-promotion accuracy drop beyond 5% or an error-rate increase beyond 50%
   over a 60-minute window are the trigger conditions in production. In this lab
   you trigger the rollback manually to rehearse the mechanism.
2. Open the **session-2-rollback** workflow and run it with your `attendee_id`.
3. The workflow reverts the shadow-mirror env-var swap: `CHAMPION_ENDPOINT_ARN`
   is restored to its pre-promotion value (the original production endpoint).
4. Confirm the workflow writes a `rollback_completed` audit entry whose
   `new_champion_endpoint_arn` equals the `previous_champion_endpoint_arn` from
   the preceding promotion entry.
5. Read both audit entries (`promotion_completed` then `rollback_completed`) and
   trace the full story: who promoted, against which criteria snapshot, and how
   the rollback returned the system to its prior state.

### Success Criterion

A `rollback_completed` audit entry exists, the shadow-mirror Lambda's
`CHAMPION_ENDPOINT_ARN` is back to the original production endpoint, and the two
audit entries together form a complete, traceable promotion-and-rollback record.

### Troubleshooting

- **Rollback runs but env vars look unchanged:** confirm a non-dry-run
  promotion actually completed in Lab 3. The rollback reverts a swap; if no swap
  occurred there is nothing to revert.
- **No `rollback_completed` audit entry:** the audit write occurs within 30
  seconds of the revert. Re-check the bucket prefix
  `audit/YYYY-MM-DD/` for today's date.
- **Audit entries missing fields:** report to the lab engineer; the audit
  schema is fixed and every entry must carry the full field set.

---

## Troubleshooting Matrix

| Symptom | Likely cause | Action |
|---|---|---|
| Endpoint not `InService` within 15 min (Lab 1) | SageMaker creation slow under account load, or quota | Re-run `session-2-deploy-challenger` (idempotent); if quota, notify the lab engineer |
| No comparison results yet — `latest.json` absent (Lab 2) | Comparison Lambda has not run its 5-minute cycle, or no traffic sent | Wait for the next cycle or invoke the comparison Lambda manually; confirm the traffic generator ran |
| `agreement_rate` 0 / high `deferred_request_ids` (Lab 2) | Challenger async outputs have not landed in S3 yet | Wait one more comparison cycle; deferred requests join once their async output arrives |
| Promotion gate refuses — "criteria not met" (Lab 3) | At least one criterion failed (this is correct) | Read the named criterion and actual vs. required values; remediate and re-run |
| Agreement too high (> 0.99) (Lab 3) | Challenger not meaningfully different from champion | Intentional guardrail — gate refuses; confirm correct challenger model |
| Agreement too low (< 0.85) (Lab 3) | Too much disagreement to trust challenger | Confirm default traffic-generator settings; re-run traffic |
| "500 observations, minimum 1000 required" (Lab 3) | Comparison window has too few joined observations | Run the traffic generator longer or at a higher rate |
| Traffic generator reports 5xx failures | Shadow-mirror or champion endpoint returned errors | Confirm both endpoints are `InService`; check shadow-mirror CloudWatch Logs; failures are counted, not fatal, so the run continues |
| Rollback shows no change (Lab 4) | No non-dry-run promotion preceded it | Complete a real promotion in Lab 3 first |
</content>
</invoke>
