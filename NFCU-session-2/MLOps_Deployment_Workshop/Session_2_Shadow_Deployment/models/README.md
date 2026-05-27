# Session 2 models

Two scikit-learn `RandomForestClassifier` pipelines trained on the public
[UCI Adult Census Income](https://archive.ics.uci.edu/ml/datasets/adult)
dataset.

| Script | Model | Hyperparameters |
|---|---|---|
| `train_champion.py` | `model-v1.0.0` | `max_depth=6, n_estimators=100, random_state=42` |
| `train_challenger.py` | `model-v1.0.1` | `max_depth=16, n_estimators=80, max_features=0.3, random_state=42` |

The challenger's hyperparameters are chosen so the two models agree on ~92% of
the test split — meaningful enough to teach a champion-challenger comparison
without a multi-week shadow run.

### Dry-run record: challenger retuning

The OpenSpec proposal illustrated the challenger with `max_depth=8,
n_estimators=150`. The lab-engineer dry-run measured that combination at **~97.5%**
agreement with the champion — too similar to teach a useful comparison and
outside the 90–94% target band. Per the design's validation requirement
(*"if it doesn't land in 90–94%, retrain model-v1.0.1 with adjusted
hyperparameters"*), the challenger was retuned. Measured candidates (agreement
with champion / test accuracy):

| `max_depth` | `n_estimators` | `max_features` | agreement | accuracy |
|---|---|---|---|---|
| 8 | 150 | (default sqrt) | 0.975 | — |
| 16 | 80 | 0.3 | **0.928** | **0.861** |
| 16 | 60 | 0.3 | 0.928 | 0.860 |
| 20 | 60 | 0.3 | 0.920 | 0.858 |

The shipped challenger uses `max_depth=16, n_estimators=80, max_features=0.3`
(agreement 0.928, accuracy 0.861 — marginally above the champion's accuracy, a
plausible candidate-improvement story).

## Usage

```bash
python train_champion.py            # writes model-v1.0.0.joblib
python train_challenger.py          # writes model-v1.0.1.joblib
python verify_agreement.py          # reports agreement rate (target 90-94%)
python package_model.py --input model-v1.0.1.joblib --output model-v1.0.1.tar.gz
```

`--dry-run` validates configuration without downloading data or training.
The dataset is cached under `models/data/` on first use.

## Protected-class fields and their limitation

The disparate-impact comparison uses two protected-class fields from UCI Adult:

- **`sex`** — binary in this dataset (`Male` / `Female`).
- **`race`** — five coarse categories.

This is a known limitation. Real-world fair-lending analysis works with richer
demographic features and more nuanced subgroup definitions. The disparate-impact
numbers this lab produces are **not** representative of production fair-lending
analysis and exist only to demonstrate the comparison mechanics. This caveat is
surfaced to attendees in `../LAB_GUIDE.md` (Lab 2) and the Slide 12 speaker notes.

UCI Adult also ships ground-truth labels, so an accuracy delta is computable
immediately. In real credit modeling, default outcomes take 12–24 months to
materialize and proxy signals (agreement rate, prediction-distribution
stability) carry the load. The lab flags this in Lab 2's debrief.
