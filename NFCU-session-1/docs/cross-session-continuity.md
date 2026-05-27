# Cross-session continuity

What the later sessions consume from Session 1, and how to perform the five-minute
trace. **If you plan to attend the later sessions, do not tear down the Session 1
endpoint, audit bucket, or model package** — they are the inputs the next sessions build
on.

---

## Session 2 — Champion-Challenger Deployment Patterns (June 4, 2026)

Reuses from Session 1:

- The **endpoint ARN** — Session 2 routes a traffic split between the champion (the
  Session 1 model) and a challenger variant on the same endpoint.
- The **model package / artifact contract** — the challenger is packaged the same way, so
  validation and signing are unchanged.
- The **audit `schema_version`** — Session 2 extends the record (adds variant/traffic
  fields) and bumps `schema_version` accordingly.

**Preserve:** the Session 1 endpoint and its endpoint configuration. Deleting the
endpoint forces a full re-provision before Session 2.

## Session 3 — Monitoring, Drift Detection & Observability (June 16, 2026)

Reuses from Session 1:

- The **endpoint ARN** and **CloudWatch log group** (`/nfcu-session-1/sagemaker`) — the
  monitoring stack attaches to these.
- The **training dataset hash** and **training run id format** — drift is measured against
  the training distribution recorded in the artifact metadata.
- The **audit bucket** — deploy events become one input to the monitoring timeline.

**Preserve:** the audit bucket and the log group. Drift baselines reference the training
data identified in the audit records.

## Session 4 — Kubernetes-Native Model Serving with KServe (June 18, 2026)

Reuses from Session 1:

- The **signed container digest** and **artifact S3 URI** — KServe pulls the same signed
  image; signature verification carries over.
- The **audit bucket location** and **training run id format** — the trace guarantee must
  survive the migration off SageMaker.
- The **KMS key** — model data stays encrypted with the same key under KServe.

**Preserve:** the signed image in ECR and the artifact in S3. KServe migrates the serving
layer, not the artifact or its provenance.

---

## The five-minute trace procedure

Goal: take any prediction the production endpoint made and walk it back to the exact
training data, using only `aws` and `jq`. Each step is one command with the shape of its
expected output.

```bash
# 0. Set the audit bucket (the AUDIT_BUCKET output of lab-platform-iac).
AUDIT_BUCKET="nfcu-session-1-audit-<account-id>"
```

**Step 1 — Find the deploy record for the date the prediction was made.**
```bash
aws s3 ls "s3://${AUDIT_BUCKET}/audit/2026-06-02/"
# Expected: one line per production deploy that day, e.g.
#   2026-06-02 14:03:11   1027 a1b2c3d4e5f6....json   (object key = git commit SHA)
```

**Step 2 — Read the audit record.**
```bash
aws s3 cp "s3://${AUDIT_BUCKET}/audit/2026-06-02/<commit-sha>.json" - | jq .
# Expected: the full JSON object, schema_version first, 15 fields. Note in particular
# training_run_id, training_dataset, artifact_s3_uri, and container_digest.
```

**Step 3 — Pull the training identifiers out of the record.**
```bash
aws s3 cp "s3://${AUDIT_BUCKET}/audit/2026-06-02/<commit-sha>.json" - \
  | jq '{training_run_id, training_dataset, artifact_s3_uri, container_digest}'
# Expected:
#   {
#     "training_run_id": "train-2026-05-27-95a0f184",
#     "training_dataset": "uci-adult-2024-snapshot",
#     "artifact_s3_uri": "s3://.../models/model-v1.0.0.tar.gz",
#     "container_digest": "sha256:..."
#   }
```

**Step 4 — Open the artifact's metadata to get the dataset hash.**
```bash
ARTIFACT=$(aws s3 cp "s3://${AUDIT_BUCKET}/audit/2026-06-02/<commit-sha>.json" - \
  | jq -r .artifact_s3_uri)
aws s3 cp "${ARTIFACT}" - | tar -xzO --wildcards '*/metadata.json' | jq .
# Expected: metadata.json including training_dataset_sha256 and the evaluation block.
```

**Step 5 — Confirm the dataset identity.**
```bash
aws s3 cp "${ARTIFACT}" - | tar -xzO --wildcards '*/metadata.json' \
  | jq '{training_run_id, training_dataset_sha256}'
# Expected: the same training_run_id as the audit record, plus the SHA256 of the exact
# dataset bytes the model was trained on. Prediction -> deploy -> artifact -> dataset,
# closed in well under five minutes.
```
