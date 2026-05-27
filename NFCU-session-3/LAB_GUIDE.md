# Lab Guide — NFCU Session 3

Reference for the lab engineer running Session 3. Covers per-attendee
provisioning, the pre-flight protocol, and per-lab timing. Attendees do not read
this; they follow the in-session prompts and the [runbooks](runbooks/).

> **Build-environment note:** Terraform here is authored and `terraform validate`-
> clean, but `plan`/`apply` require a live lab sandbox with AWS credentials. The
> commands below are the real session-day commands; they are not exercised in the
> build environment. See [`../RUN_CONFIG.md`](../RUN_CONFIG.md).

---

## Roles and timing

| Lab | Minutes | What attendees do |
|-----|---------|-------------------|
| Lab 1 | 12 | Instrument the endpoint; apply dashboard + alarms; confirm infra row populates |
| Lab 2 | 15 | Invoke drift-simulator; watch per-feature PSI cross 0.25; drift alarm fires |
| Lab 3 | 15 | Run evidently-runner (report) + nannyml-runner (estimated AUC) |
| Lab 4 | 15 | Trigger assigned incident scenario; route it with the matching runbook |

The 6-minute schedule buffer depends on Lab 1 not spilling. The **only** thing
that prevents spillover is the pre-flight protocol below. Staff 2 assistants for a
30-person cohort.

---

## Pre-flight protocol (run before attendees arrive)

1. **Verify all 30 sandboxes:**
   ```bash
   scripts/verify-lab-readiness.sh --cohort cohort.txt
   ```
   `cohort.txt` is one `attendee_id` per line. The script prints a green/red table
   and, for each red row, the specific failure mode (endpoint missing, alarm
   misconfigured, dashboard not provisioned).

2. **Restore any red endpoint** (idempotent; no-op on healthy ones):
   ```bash
   scripts/restore-session2-endpoint.sh --attendee-id <id>
   ```
   Budget: ≤ 4 minutes per endpoint, end-to-end. Safe to run repeatedly.

3. **Re-run the readiness check** until the table is all green.

---

## Per-Attendee Provisioning

Each attendee needs: two S3 buckets, an IAM role/policy, five Lambdas, an
EventBridge 2-minute schedule, a CloudWatch dashboard, and three alarms + an SNS
topic. Target: **≤ 15 minutes** per attendee following these steps.

### Option A — GitHub Actions (batch)

The workflow at `.github/workflows/nfcu-session-3-deploy-monitoring.yml` is
parameterized on `attendee_id`. Trigger it per attendee via `workflow_dispatch`,
or fan out across the cohort via `repository_dispatch`.

> This workflow is nested under `NFCU-session-3/` for self-containment and will
> not auto-run as repo CI; copy it to the repo-root `.github/workflows/` in a live
> CI repo if you want GitHub to execute it. See `../RUN_CONFIG.md`.

### Option B — Terraform directly (single attendee)

```bash
cd NFCU-session-3/infra
terraform init
terraform workspace new "$ATTENDEE_ID" 2>/dev/null || terraform workspace select "$ATTENDEE_ID"
terraform apply -var="attendee_id=$ATTENDEE_ID" -var="region=us-east-1"
```

This provisions the buckets, IAM, Lambdas, and EventBridge schedule. Then apply
the monitoring layer:

```bash
cd ../monitoring
terraform apply -var="attendee_id=$ATTENDEE_ID"
aws cloudwatch put-dashboard \
  --dashboard-name "workshop-lab-${ATTENDEE_ID}" \
  --dashboard-body "file://dashboard.rendered.json"
```

### Then upload the reference distribution

The reference distribution is captured **once** at build time (not per attendee)
by `scripts/capture-reference-distribution.py`. Upload the resulting
`reference.parquet` to each attendee's baseline bucket:

```bash
aws s3 cp reference.parquet "s3://workshop-lab-${ATTENDEE_ID}-baseline/reference.parquet"
```

### Verify

```bash
aws cloudwatch describe-alarms --alarm-name-prefix "workshop-lab-${ATTENDEE_ID}"
# expect exactly three alarms, all OK:
#   Drift-PSI-<id>, Latency-P95-<id>, ErrorRate-<id>
```

---

## Teardown

Sandboxes are preserved through **June 18** (Session 4 depends on the endpoints
remaining `InService`). Do not tear down endpoints after Session 3. Session
3-specific resources (Lambdas, buckets, alarms) may be removed with
`terraform destroy` per workspace after June 18.

---

## Model-risk framing (D12)

When you narrate the dashboard and runbooks, frame PSI and the routing rule as
*aligned with model-risk principles*. Do **not** claim NCUA or FFIEC compliance,
and do not refer to NFCU as a "bank." This material is a monitoring pattern, not a
compliance attestation.
