# Lab Assistant Briefing — NFCU Session 3

For the 2 assistants supporting the 30-person cohort (task 10.7). Read this before
session day. Operational detail is in [LAB_GUIDE.md](LAB_GUIDE.md).

## 1. Lab 1 pre-flight protocol (most important)

The whole schedule's 6-minute buffer depends on Lab 1 **not** spilling, and the
only thing preventing spillover is pre-flight. Before attendees arrive:

1. Run `scripts/verify-lab-readiness.sh --cohort cohort.txt` — green/red table.
2. For every **red** row, run `scripts/restore-session2-endpoint.sh --attendee-id <id>`
   (idempotent, ≤ 4 min; no-op on healthy endpoints).
3. Re-run the readiness check until **all green**.

Split the cohort between the two of you (15 each). Do not let an attendee start
Lab 1 against a red sandbox.

## 2. Round-robin scenario distribution (for the Slide 18 debrief)

Incidents are assigned **round-robin**, not randomly, so the debrief lands:

| Scenario | Count (of 30) |
|----------|---------------|
| 1 feature_pipeline_broken | 6 |
| 2 data_drift | 6 |
| 3 prediction_drift_isolated | 6 |
| 4 latency_degradation | 6 |
| 5 concept_drift_confirmed | 6 |

When Michael asks "who got the feature pipeline incident?" on Slide 18, expect ~6
hands. If the distribution looks skewed, the lab platform passed the wrong
`attendee_index` — flag it.

## 3. The incident simulator is simulated (say this out loud)

The incident alarms are **real-sounding but simulated** — no production system is
affected and nothing pages an external service. The SNS topic is visible in the
dashboard but is **not** wired to PagerDuty/Slack. Reassure attendees who get
nervous when "their" alarm goes red; that's the lesson, not an outage. Every
scenario auto-cleans up within 15 minutes.

## 4. Framing guardrail (D12)

When you narrate dashboards or runbooks, frame PSI and the routing rule as
*aligned with model-risk principles*. Do not state that the lab constitutes
regulatory compliance, and do not call NFCU a "bank." This is a monitoring
pattern, not an attestation.

## 5. Quick triage if an attendee is stuck

- Dashboard top row empty → endpoint not receiving traffic; check Lab 1 setup.
- Drift alarm not firing in Lab 2 → confirm the drift-simulator was invoked; the
  detector runs every 2 min, so allow up to ~5 min.
- Evidently/NannyML Lambda errors → usually the current window is empty; make sure
  the attendee sent traffic first.
