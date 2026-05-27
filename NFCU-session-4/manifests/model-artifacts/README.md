# Model Artifacts

The two XGBoost models the labs serve. **They are not committed to git** — `.bst` files are
binary build outputs. You generate them deterministically instead:

```bash
python generate-xgboost-models.py     # writes model-v1.0.0/model.bst and model-v1.0.1/model.bst
```

## The two versions

Both are binary classifiers on the UCI Adult Census Income dataset (predict income > $50K).
They differ only in hyperparameters, so the Lab 4 canary shows a real difference:

| Version | max_depth | n_estimators | learning_rate | Role |
|---|---|---|---|---|
| `model-v1.0.0` | 4 | 100 | 0.3 | The deployed model (Lab 1) |
| `model-v1.0.1` | 6 | 200 | 0.2 | The canary candidate (Lab 4) |

## Determinism

The generator is seeded and single-threaded. Re-running it with the same `--seed` **and the
same xgboost version** produces byte-identical `model.bst` files. That is what keeps the curl
request/response examples in `attendee-guide/` accurate. If you change the seed or the
library version, regenerate and re-capture the example outputs.

## Getting the models to the cluster

- **EKS:** `bash upload-to-s3.sh` reads the bucket name from `terraform output` and uploads
  both versions. The Lab manifests' `storageUri` then points at `s3://<bucket>/model-v1.0.0`.
- **Local kind:** load `model-v1.0.0/` onto a PVC named `model-store` (e.g., copy into a
  small helper pod that mounts the PVC), and set `storageUri: pvc://model-store/model-v1.0.0`.

## Requirements

`xgboost`, `pandas`, `scikit-learn` on Python 3.12+. The first run downloads the dataset
from OpenML and caches it under `~/scikit_learn_data`.
