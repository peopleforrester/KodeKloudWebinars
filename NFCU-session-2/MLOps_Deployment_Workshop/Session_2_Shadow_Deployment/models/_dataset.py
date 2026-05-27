# ABOUTME: Shared UCI Adult Census Income loading/preprocessing for the lab models.
# ABOUTME: Downloads and caches the public dataset; builds the champion/challenger pipeline.
# SPDX-License-Identifier: Apache-2.0
"""UCI Adult Census Income dataset helpers.

The dataset is public and synthetic-safe. It is downloaded on first use from
the UCI machine learning repository and cached locally. Both the champion and
challenger trainers, and the agreement-verification helper, build on this
module so preprocessing is identical across all three.
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

_BASE_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/"
_FILES = ("adult.data", "adult.test")

COLUMN_NAMES = [
    "age",
    "workclass",
    "fnlwgt",
    "education",
    "education-num",
    "marital-status",
    "occupation",
    "relationship",
    "race",
    "sex",
    "capital-gain",
    "capital-loss",
    "hours-per-week",
    "native-country",
    "income",
]

NUMERIC_FEATURES = [
    "age",
    "fnlwgt",
    "education-num",
    "capital-gain",
    "capital-loss",
    "hours-per-week",
]
CATEGORICAL_FEATURES = [
    "workclass",
    "education",
    "marital-status",
    "occupation",
    "relationship",
    "race",
    "sex",
    "native-country",
]

# Protected-class fields surfaced in the disparate-impact comparison. UCI Adult
# only carries binary `sex` and a coarse `race`; this limitation is documented
# in the model README and surfaced to attendees in LAB_GUIDE.md.
PROTECTED_FEATURES = ["sex", "race"]

TARGET = "income"


def default_data_dir() -> Path:
    """Return the on-disk cache directory for the dataset."""
    return Path(__file__).resolve().parent / "data"


def download_adult(data_dir: Path) -> None:
    """Download the UCI Adult files into ``data_dir`` if not already cached.

    Args:
        data_dir: Directory in which the raw ``adult.data`` / ``adult.test``
            files are cached.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    for name in _FILES:
        target = data_dir / name
        if target.exists():
            continue
        url = _BASE_URL + name
        print(f"Downloading {url} ...", file=sys.stderr)
        with urllib.request.urlopen(url) as response:  # noqa: S310 (trusted UCI host)
            payload = response.read()
        target.write_bytes(payload)
        print(f"  saved {len(payload):,} bytes -> {target}", file=sys.stderr)


def _read_split(path: Path, *, skiprows: int) -> pd.DataFrame:
    """Read one Adult split, normalizing whitespace and label punctuation."""
    frame = pd.read_csv(
        path,
        header=None,
        names=COLUMN_NAMES,
        skiprows=skiprows,
        skipinitialspace=True,
        na_values="?",
        comment="|",
    )
    frame = frame.dropna()
    # adult.test labels carry a trailing period (e.g. "<=50K.").
    frame[TARGET] = frame[TARGET].str.rstrip(".").str.strip()
    return frame


def load_adult(
    data_dir: Path | None = None,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """Load and preprocess the Adult train/test splits.

    Args:
        data_dir: Optional cache directory. Defaults to ``models/data/``.

    Returns:
        Tuple ``(X_train, y_train, X_test, y_test)``. Targets are integer
        labels (1 for ``>50K``, 0 otherwise).
    """
    data_dir = data_dir or default_data_dir()
    download_adult(data_dir)
    train = _read_split(data_dir / "adult.data", skiprows=0)
    test = _read_split(data_dir / "adult.test", skiprows=1)

    feature_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    x_train = train[feature_cols].reset_index(drop=True)
    x_test = test[feature_cols].reset_index(drop=True)
    y_train = (train[TARGET] == ">50K").astype(int).reset_index(drop=True)
    y_test = (test[TARGET] == ">50K").astype(int).reset_index(drop=True)
    return x_train, y_train, x_test, y_test


def build_pipeline(estimator: RandomForestClassifier) -> Pipeline:
    """Wrap ``estimator`` in the shared preprocessing pipeline.

    Args:
        estimator: A fitted-or-unfitted classifier to place at the end of the
            pipeline.

    Returns:
        An sklearn :class:`~sklearn.pipeline.Pipeline` with one-hot encoding for
        categorical features and passthrough for numeric features.
    """
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", NUMERIC_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
        ]
    )
    return Pipeline(steps=[("preprocess", preprocessor), ("model", estimator)])
