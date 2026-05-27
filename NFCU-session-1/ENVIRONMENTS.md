# Environments: dev → staging → production

Session 1 ships **three** deployment environments. One immutable model artifact is
promoted through them in order — **dev → staging → production** — and the *same
signed container digest* moves forward at each step (later stages never rebuild).

If you followed an older workshop doc that only mentioned dev and prod: **staging is
real and intentional.** Its job is to prove the already-signed dev image deploys
cleanly to a fresh environment without a rebuild.

## At a glance

| Environment | Terraform dir | Workflow | Trigger | Approval gate |
|---|---|---|---|---|
| **dev** | `terraform/environments/dev/` | `nfcu-session-1-deploy-dev.yml` | Push to `main` (paths under `NFCU-session-1/**`) | None |
| **staging** | `terraform/environments/staging/` | `nfcu-session-1-deploy-staging.yml` | A **`promote-to-staging`** PR is merged into `main` | None |
| **production** | `terraform/environments/production/` | `nfcu-session-1-deploy-production.yml` | Manual `workflow_dispatch` with a `change_ticket_reference` | **Required reviewer** (GitHub Environment `nfcu-session-1-production`) |

All three workflows authenticate to AWS via OIDC (no static keys), are path-filtered to
`NFCU-session-1/**`, and run the validation gate (`validate.py`) first.

## What each stage runs

**dev** — `validate` → `containerize` (optional) → `terraform apply (dev)`
- The container build/scan/sign stage is gated by the workflow-level env
  `ENABLE_CONTAINER_STAGE` (default `"false"`). Flip it to `"true"` to run the full
  build → Trivy scan → Cosign sign → push, which emits the signed image digest.
- With the stage off, dev deploys a pre-existing signed image (`vars.CONTAINER_IMAGE_URI`).

**staging** — `validate` → `verify-container` → `terraform apply (staging)`
- Triggered only when a PR whose head branch is `promote-to-staging` is **merged** into
  `main` (`pull_request: closed` + `merged == true` + `head_ref == 'promote-to-staging'`).
- `verify-container` runs `cosign verify` against the **digest from the dev build** and
  **does not rebuild**. A failed verification blocks the apply.

**production** — `check-ticket` → `validate` → `verify-container` → `terraform apply (production)` → `audit-trail`
- Manual run only. The required input `change_ticket_reference` must match
  `^(LAB|CHG|TICKET|DEMO)-[0-9]+$` or the run fails immediately.
- The `deploy-production` job is bound to the `nfcu-session-1-production` GitHub
  Environment, so **at least one reviewer must approve** at the gate before it proceeds.
- It also runs a separation-of-duties check (approver vs. change author — informational
  on a single-user demo; see `LAB_GUIDE.md`), then writes the immutable audit record
  (`audit-trail.py`) as the final step. The deploy is not considered successful without it.

## Promotion flow

```
commit to main ─▶ DEV   (validate, optional build/scan/sign, apply)
                   │
       open & merge a `promote-to-staging` PR into main
                   ▼
                 STAGING (validate, verify signed digest — no rebuild, apply)
                   │
       manual workflow_dispatch + change ticket + reviewer approval
                   ▼
                 PRODUCTION (ticket check, validate, verify, apply, audit-trail)
```

The model version is immutable semver throughout; `validate.py` rejects mutable
references (`latest`, `prod`, `current`, `stable`, `main`) before anything is built or
deployed, in every environment.

## GitHub Environments setup

Three GitHub Environments back these workflows — `nfcu-session-1-dev`,
`nfcu-session-1-staging`, `nfcu-session-1-production`. Only **production** carries a
required reviewer; dev and staging have none. They are created manually after applying
`lab-platform-iac/`; see the **Prerequisites** section of [LAB_GUIDE.md](LAB_GUIDE.md).

For Session 1 the three environments differ only by `name` and the injected
`model_version` — they are deliberately aligned so Sessions 2–4 can diverge them
(champion-challenger, monitoring, KServe).
