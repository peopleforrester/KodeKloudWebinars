# Operations Runbook

Everything the lab engineering team and the speaker need to run Session 4 safely — from
sign-off gates to the minute-by-minute on the day to tearing it all down.

## Contents

| Doc | Use it for |
|---|---|
| [`definition-of-done.md`](definition-of-done.md) | The five dated gates. Sign off mechanically; any "not done" blocks session day. |
| [`dry-run-checklist.md`](dry-run-checklist.md) | The June 13 end-to-end validation (DoD Gate 3). |
| [`day-of-operations.md`](day-of-operations.md) | T-60 min → T+30 min timeline for 2026-06-18. |
| [`troubleshooting-matrix.md`](troubleshooting-matrix.md) | 14 known symptoms with exact fixes and confirmation steps. |
| [`cleanup-automation.md`](cleanup-automation.md) | What dies at T+30, what persists 24h, what's gone by 2026-06-20. |
| [`speaker-aws-spend.md`](speaker-aws-spend.md) | What the EKS demo cluster costs; how to stop the meter. |

## Key dates

| Date | Gate |
|---|---|
| 2026-06-02 | Pre-provisioning done |
| 2026-06-06 | Per-attendee provisioning done (lab platform) |
| 2026-06-13 | Dry run green; images pre-pulled |
| 2026-06-18 | Session day (10:00 AM ET) |
| 2026-06-20 | Full decommission verified |

## The two things most likely to go wrong

1. **The TinyLlama image isn't pre-pulled.** Hugging Face download at build is the single
   most fragile dependency. Pre-pull both TinyLlama and distilGPT-2 to every node by the
   June 13 gate, and have the fallback ready.
2. **The cluster doesn't get torn down.** `terraform destroy` is manual. It's on the
   post-session checklist in two places (`cleanup-automation.md` and DoD Gate 5) on purpose.
