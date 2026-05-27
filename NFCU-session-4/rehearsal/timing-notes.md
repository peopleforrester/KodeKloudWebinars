# Timing Notes

Step durations for the rehearsal scripts. **The "target" columns are estimates** derived
from the session goals and component norms. The "actual" columns are blank on purpose —
fill them in during the 2026-06-13 dry run (DoD Gate 3) so the day-of timing is grounded in
real numbers, not guesses.

## Local (kind) — `run-full-session-local.sh`

Goal: cold start to teardown in **under 30 minutes** on a 16 GB / 4-core laptop.

| Step | Target | Actual (fill in) |
|---|---|---|
| kind create + add-ons bootstrap | 10–15 min | |
| Generate model artifacts | <1 min | |
| Build predictor + load into kind | 3–6 min | |
| Stage models onto PVC | <1 min | |
| Deploy labs 1–4 + wait Ready | 2–4 min | |
| Smoke + k6 (xgboost, tinyllama, canary) | 5–8 min | |
| Teardown | <1 min | |
| **Total** | **~25–30 min** | |

## EKS — `run-full-session-eks.sh`

Goals: `terraform apply` under **25 min**; add-ons + labs under **15 min**.

| Step | Target | Actual (fill in) |
|---|---|---|
| terraform apply (VPC + EKS + IRSA + S3) | 15–25 min | |
| Add-ons bootstrap + verify | 10–15 min | |
| Models → S3, predictor → ECR | 5–10 min | |
| Deploy labs 1–4 + wait Ready | 3–6 min | |
| Smoke + k6 + canary | 8–12 min | |
| terraform destroy | 10–15 min | |
| **Total (excl. destroy)** | **~40–60 min** | |

## Cold-start times to record (matter for the live demo)

| Endpoint | Target | Actual (fill in) |
|---|---|---|
| Lab 1 XGBoost — first request after scale-to-zero | <15 s | |
| Lab 3 TinyLlama — Ready after apply | <120 s | |
| Lab 3 TinyLlama — first completion after scale-to-zero | <30 s | |

## Notes column

Use this space during the dry run to record anything that ran long, any retry needed, and
the laptop/instance specs the numbers were measured on (so they're comparable next time).
