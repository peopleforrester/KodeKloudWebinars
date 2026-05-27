#!/usr/bin/env python3
# ABOUTME: Build the baseline UCI Adult classifier and package it as model.tar.gz.
# ABOUTME: Produces a SageMaker-compatible sklearn artifact for the restore script.
"""Build the Session 1/2 baseline model artifact (task 8.1).

Trains a small logistic-regression pipeline on the eight lab features of the UCI
Adult training data, serializes it with joblib, and packages it together with a
SageMaker sklearn-container ``inference.py`` into ``model.tar.gz``.

The artifact layout matches the SageMaker sklearn container contract:

    model.tar.gz
    ├── model.joblib        # the fitted pipeline
    └── code/
        └── inference.py    # model_fn / input_fn / predict_fn / output_fn
"""

import argparse
import io
import logging
import tarfile
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("build-baseline-model")

NUMERIC = ["age", "education_num", "hours_per_week"]
CATEGORICAL = ["workclass", "marital_status", "occupation", "race", "sex"]
FEATURES = ["age", "workclass", "education_num", "marital_status",
            "occupation", "race", "sex", "hours_per_week"]
UCI_COLUMNS = [
    "age", "workclass", "fnlwgt", "education", "education_num",
    "marital_status", "occupation", "relationship", "race", "sex",
    "capital_gain", "capital_loss", "hours_per_week", "native_country", "income",
]

INFERENCE_PY = '''# ABOUTME: SageMaker sklearn-container inference handlers for the UCI Adult model.
# ABOUTME: Loads the joblib pipeline and serves CSV in / CSV (proba,label) out.
import io
import os

import joblib
import pandas as pd

FEATURES = ["age", "workclass", "education_num", "marital_status",
            "occupation", "race", "sex", "hours_per_week"]


def model_fn(model_dir):
    return joblib.load(os.path.join(model_dir, "model.joblib"))


def input_fn(request_body, content_type="text/csv"):
    if content_type != "text/csv":
        raise ValueError(f"Unsupported content type: {content_type}")
    rows = [line for line in request_body.strip().splitlines() if line]
    data = [dict(zip(FEATURES, r.split(","))) for r in rows]
    df = pd.DataFrame(data)
    for col in ["age", "education_num", "hours_per_week"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def predict_fn(df, model):
    proba = model.predict_proba(df)[:, 1]
    label = (proba > 0.5).astype(int)
    return list(zip(proba.tolist(), label.tolist()))


def output_fn(prediction, accept="text/csv"):
    return "\\n".join(f"{p:.6f},{l}" for p, l in prediction), "text/csv"
'''


def _load_training_data(source: Path) -> pd.DataFrame:
    df = pd.read_csv(source, header=None, names=UCI_COLUMNS, skipinitialspace=True,
                     comment="|", na_values=["?"])
    df["income"] = df["income"].astype(str).str.rstrip(".").str.strip()
    df = df[FEATURES + ["income"]].dropna()
    df["label"] = (df["income"] == ">50K").astype(int)
    return df


def build_pipeline() -> Pipeline:
    pre = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
    ])
    return Pipeline([("pre", pre), ("clf", LogisticRegression(max_iter=1000))])


def main(argv=None) -> int:
    here = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", default=str(here / "shared/fixtures/uci-adult/adult.test"),
                        help="UCI training/test CSV to fit on (default: bundled fixture)")
    parser.add_argument("--out", default=str(here / "shared/baseline-models/session-1-2-uci-adult/model.tar.gz"))
    args = parser.parse_args(argv)

    logger.info("Loading training data: %s", args.train)
    df = _load_training_data(Path(args.train))
    logger.info("Training on %d rows (%.1f%% positive)", len(df), 100 * df["label"].mean())

    pipeline = build_pipeline()
    pipeline.fit(df[FEATURES], df["label"])
    train_acc = pipeline.score(df[FEATURES], df["label"])
    logger.info("Training accuracy: %.4f", train_acc)

    # Serialize and package as model.tar.gz with the inference code.
    model_bytes = io.BytesIO()
    joblib.dump(pipeline, model_bytes)
    model_bytes.seek(0)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(out, "w:gz") as tar:
        info = tarfile.TarInfo("model.joblib")
        info.size = len(model_bytes.getvalue())
        tar.addfile(info, io.BytesIO(model_bytes.getvalue()))

        code = INFERENCE_PY.encode("utf-8")
        info = tarfile.TarInfo("code/inference.py")
        info.size = len(code)
        tar.addfile(info, io.BytesIO(code))

    logger.info("Wrote %s (%d bytes)", out, out.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
