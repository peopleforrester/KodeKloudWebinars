# Baseline model artifact (session-local)

**Ownership:** session-local to NFCU Session 3. This is a Session 3-owned copy of
the Session 1/2 baseline model so the restore script works even if Session 1 has
not been built. A future session may copy or reference it; that is its call.

## What this is

`model.tar.gz` — a SageMaker-compatible sklearn artifact: a logistic-regression
pipeline (StandardScaler on numerics + one-hot on categoricals) over the eight lab
features, predicting UCI Adult income (`>50K` vs `<=50K`). Layout:

```
model.tar.gz
├── model.joblib        # the fitted sklearn pipeline
└── code/inference.py   # model_fn / input_fn (CSV) / predict_fn / output_fn (CSV: proba,label)
```

It serves CSV in (`age,workclass,education_num,marital_status,occupation,race,sex,hours_per_week`)
and returns `predicted_proba,predicted_label` per row.

## How it was built

Reproducible via `scripts/build-baseline-model.py`, trained on
`shared/fixtures/uci-adult/adult.test`. Training accuracy ≈ 0.83. Rebuild with:

```bash
python scripts/build-baseline-model.py
```

## How it is used

`scripts/restore-session2-endpoint.sh` uploads this artifact to a shared S3 bucket
(see Open Question 3) and creates a SageMaker model + endpoint from it when an
attendee's Session 1/2 endpoint is missing or unhealthy. It is **not** the
production training pipeline — it is a recovery stand-in that classifies the same
task with the same input contract.
