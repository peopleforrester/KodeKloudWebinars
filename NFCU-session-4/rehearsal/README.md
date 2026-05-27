# Rehearsal

End-to-end scripts that run the whole session — bootstrap, deploy all four labs, drive the
load tests, and tear down — so the speaker can rehearse without surprises. Two paths,
sharing the same manifests, predictor, and k6 scripts.

## Two paths

| Script | Where | Cost | Use it for |
|---|---|---|---|
| `run-full-session-local.sh` | kind on your laptop | none | Iterating on the flow; the fast feedback loop |
| `run-full-session-eks.sh` | your EKS account | ~$5–$10 (see spend doc) | A faithful dress rehearsal of the live demo |

## Local

```bash
bash run-full-session-local.sh
```

Brings up kind + add-ons, generates and stages the models on a PVC, builds and side-loads
the predictor image, deploys labs 1–4, runs the smoke and k6 tests, and tears the cluster
down. Target: **under 30 minutes** on a 16 GB / 4-core laptop. Prereqs: `docker`, `kind`,
`kubectl`, `helm`, `k6`, `python3`.

## EKS

```bash
export BASE_URL=http://<your-nlb-address>     # from the kourier Service / NLB
bash run-full-session-eks.sh                  # tears down on exit unless KEEP_CLUSTER=1
```

`terraform apply` → bootstrap → models to S3 → predictor to ECR → deploy → k6 → canary →
`terraform destroy`. **It always tears down on exit** (even on failure) unless you set
`KEEP_CLUSTER=1` — the forgotten cluster is the costly mistake this guards against. Prereqs:
the EKS prerequisites in [`../cluster/eks/`](../cluster/eks/README.md) plus `k6`.

## Timing

Record real step durations during the June 13 dry run in
[`timing-notes.md`](timing-notes.md) — the targets there are estimates until you do.

## Relationship to the runbook

These scripts automate what the [`dry-run-checklist`](../runbook/dry-run-checklist.md) does
by hand. Run the script to get through it fast; use the checklist to confirm each acceptance
point and to record sign-off.
