#!/usr/bin/env python3
# ABOUTME: Deterministically trains the two XGBoost models (v1.0.0, v1.0.1) the labs serve.
# ABOUTME: Same seed + same library versions => byte-identical model.bst files.
"""Generate the Session 4 XGBoost model artifacts.

Trains two versions of a binary classifier on the UCI Adult Census Income dataset
(predict whether income exceeds $50K). The two versions differ only in hyperparameters,
so the Lab 4 canary surfaces a real behavioral difference between them.

Determinism: a fixed seed and single-threaded training make each model reproducible.
Re-running with the same seed and the same xgboost version produces byte-identical
``model.bst`` files, which keeps the curl examples in the attendee guide accurate.

Usage:
    python generate-xgboost-models.py [--output-dir DIR] [--seed N]

Requires (see pyproject in predictors/ for pins): xgboost, pandas, scikit-learn.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
import xgboost as xgb
from sklearn.datasets import fetch_openml

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
logger = logging.getLogger("generate-models")

DEFAULT_SEED = 42

# Hyperparameters per version. v1.0.1 is a deeper, larger ensemble — close enough to
# v1.0.0 to be a believable upgrade, different enough that the canary split is visible.
MODEL_VERSIONS: dict[str, dict[str, int | float | str]] = {
    "model-v1.0.0": {"max_depth": 4, "n_estimators": 100, "learning_rate": 0.3},
    "model-v1.0.1": {"max_depth": 6, "n_estimators": 200, "learning_rate": 0.2},
}


def load_dataset() -> tuple[pd.DataFrame, pd.Series]:
    """Load and encode the UCI Adult Census Income dataset.

    Returns:
        A tuple ``(X, y)`` of integer-encoded features and a 0/1 target where 1 means
        income > $50K.

    Raises:
        RuntimeError: If the dataset cannot be fetched.
    """
    logger.info("Fetching UCI Adult Census Income dataset (cached after first run)...")
    try:
        bunch = fetch_openml("adult", version=2, as_frame=True)
    except Exception as exc:  # network or OpenML availability
        raise RuntimeError(f"Could not fetch the Adult dataset: {exc}") from exc

    frame = bunch.frame.copy()
    target_col = bunch.target.name  # "class"

    # Encode categoricals to deterministic integer codes; XGBoost handles them as numeric.
    y = (frame[target_col].astype(str).str.strip().str.startswith(">50K")).astype(int)
    features = frame.drop(columns=[target_col])
    for col in features.columns:
        if str(features[col].dtype) in ("category", "object"):
            features[col] = features[col].astype("category").cat.codes
    features = features.fillna(-1)

    logger.info("Loaded %d rows, %d features.", len(features), features.shape[1])
    return features, y


def train_model(
    features: pd.DataFrame, target: pd.Series, params: dict, seed: int
) -> xgb.XGBClassifier:
    """Train one XGBoost classifier deterministically.

    Args:
        features: Encoded feature matrix.
        target: Binary target series.
        params: Version-specific hyperparameters.
        seed: Random seed shared by all versions for reproducibility.

    Returns:
        The fitted classifier.
    """
    model = xgb.XGBClassifier(
        max_depth=int(params["max_depth"]),
        n_estimators=int(params["n_estimators"]),
        learning_rate=float(params["learning_rate"]),
        objective="binary:logistic",
        eval_metric="logloss",
        tree_method="hist",
        n_jobs=1,          # single-threaded => deterministic, byte-identical output
        random_state=seed,
    )
    model.fit(features, target)
    return model


def main(argv: list[str] | None = None) -> int:
    """Train and save both model versions. Returns a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Directory to write model-v*/model.bst into (default: this script's dir).",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed.")
    args = parser.parse_args(argv)

    features, target = load_dataset()

    total = len(MODEL_VERSIONS)
    for i, (version, params) in enumerate(MODEL_VERSIONS.items(), start=1):
        logger.info("[%d/%d] Training %s (%s)...", i, total, version, params)
        model = train_model(features, target, params, args.seed)

        out_dir = args.output_dir / version
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "model.bst"
        model.get_booster().save_model(str(out_path))
        logger.info("[%d/%d] Wrote %s", i, total, out_path)

    logger.info("Done. Both model versions written under %s", args.output_dir)
    logger.info("Next: bash upload-to-s3.sh  (EKS)  — or load onto a PVC for local kind.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
