# Environments: champion ↔ challenger (shadow deployment)

Session 2 does **not** use a dev/staging/production ladder. Its environment model is
**two roles on the same live endpoint** plus a per-attendee sandbox:

- **champion** — the model currently serving real customer traffic.
- **challenger** — the candidate model, deployed in **shadow**: it receives *mirrored
  copies* of live requests and its predictions are logged and compared, but **never
  returned to customers**. Zero customer impact while it is evaluated.

The "promotion" here is challenger → champion, gated by measured evidence — not a push
through staging.

## Roles at a glance

| Role | What it is | Customer-facing? | Becomes champion via |
|---|---|---|---|
| **champion** | Live production model | Yes | — |
| **challenger (shadow)** | Candidate under evaluation on mirrored traffic | No | the promote workflow, if criteria pass |

## The flow

```
deploy challenger (shadow) ─▶ mirror live traffic ─▶ compare ─▶ promote (gated) ─▶ champion
                                                          │
                                                          └▶ rollback (if it regresses)
```

1. **Deploy challenger** — `session-2-deploy-challenger.yml`. The shadow-mirror Lambda
   duplicates live traffic to the challenger; the comparison Lambda scores agreement,
   latency, and disparate impact against the champion.
2. **Evaluate** against [`config/promotion-criteria.yaml`](MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/config/promotion-criteria.yaml):
   agreement rate 0.85–0.99, challenger p95 latency ≤ 200 ms (and ≤ 20% over champion),
   the four-fifths disparate-impact rule, and ≥ 1000 observations (≥ 100 per protected group).
3. **Promote** — `session-2-promote-challenger.yml`, bound to the **`promotion` GitHub
   Environment** (approval gate). The challenger takes over as champion.
4. **Rollback** — `session-2-rollback.yml` if, within 60 minutes, post-promotion accuracy
   drops > 5% or error rate rises > 50% (see `rollback_criteria` in the same file).

## Provisioning

Per-attendee and **opt-in**: nothing touches AWS until you run a
`provision-attendee.sh`. `make validate` runs everything that does **not** touch AWS.

## A note on the workflows

These workflows live under `NFCU-session-2/.github/workflows/` because this directory is
a self-contained workshop root. GitHub Actions only executes workflows from the
*repository* root `.github/workflows/` (where Session 1's live pipelines run), so the
Session 2 workflows here are **illustrative and runnable on demand via `workflow_dispatch`
in a fork that promotes them to its root** — they are not wired as live CI in this
archive. The `promotion` environment gate is the mechanism that enforces human approval
on promote.
