#!/usr/bin/env python3
# ABOUTME: Trains the UCI Adult Census XGBoost demo classifier and packages it as a
# ABOUTME: deterministic model-v1.0.0.tar.gz artifact for the NFCU Session 1 pipeline.
"""Train the sample income classifier and emit a reproducible model artifact.

The script downloads the UCI Adult Census dataset, trains an XGBoost binary
classifier predicting whether income exceeds $50K, and packages the model plus
its metadata into ``model-v1.0.0.tar.gz``. Two runs on identical hardware produce
byte-identical tarballs (fixed seed, single-threaded training, zeroed tar/gzip
timestamps), so the artifact SHA256 is a stable build identifier.

Run ``--dry-run`` to exercise download and preprocessing without writing the
artifact.

This is a teaching example. See the generated ``model_card.md`` for the model's
deliberate limitations — it is not suitable for any production credit decision.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import logging
import os
import sys
import tarfile
import tempfile
import urllib.request
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, f1_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOG = logging.getLogger("train-sample-model")

# --- Reproducibility constants ----------------------------------------------
RANDOM_STATE = 42
MODEL_VERSION = "1.0.0"
MODEL_DIR = f"model-v{MODEL_VERSION}"
ARTIFACT_NAME = f"model-v{MODEL_VERSION}.tar.gz"
DATASET_LABEL = "uci-adult-2024-snapshot"

# UCI Adult Census raw files (CC BY 4.0). Mirror of dataset id 2.
DATA_BASE = "https://archive.ics.uci.edu/ml/machine-learning-databases/adult"
TRAIN_URL = f"{DATA_BASE}/adult.data"
TEST_URL = f"{DATA_BASE}/adult.test"

# Full UCI Adult column layout (the raw files are headerless).
COLUMNS = [
    "age", "workclass", "fnlwgt", "education", "education_num",
    "marital_status", "occupation", "relationship", "race", "sex",
    "capital_gain", "capital_loss", "hours_per_week", "native_country", "income",
]

# The eight features the served model exposes (matches signature.json). Order is
# significant: training and inference must encode columns in exactly this order.
NUMERIC_FEATURES = ["age", "hours_per_week"]
CATEGORICAL_FEATURES = ["workclass", "education", "marital_status", "occupation", "race", "sex"]
FEATURE_ORDER = ["age", "hours_per_week", "workclass", "education", "marital_status", "occupation", "race", "sex"]

# Hardcoded category vocabularies from the UCI Adult data dictionary, sorted for a
# stable ordinal encoding. Unknown values encode to -1. These are the single source
# of truth: the generated inference.py is built from the same dict, so the training
# and serving encoders cannot drift.
CATEGORIES: dict[str, list[str]] = {
    "workclass": sorted([
        "Private", "Self-emp-not-inc", "Self-emp-inc", "Federal-gov",
        "Local-gov", "State-gov", "Without-pay", "Never-worked",
    ]),
    "education": sorted([
        "Bachelors", "Some-college", "11th", "HS-grad", "Prof-school",
        "Assoc-acdm", "Assoc-voc", "9th", "7th-8th", "12th", "Masters",
        "1st-4th", "10th", "Doctorate", "5th-6th", "Preschool",
    ]),
    "marital_status": sorted([
        "Married-civ-spouse", "Divorced", "Never-married", "Separated",
        "Widowed", "Married-spouse-absent", "Married-AF-spouse",
    ]),
    "occupation": sorted([
        "Tech-support", "Craft-repair", "Other-service", "Sales",
        "Exec-managerial", "Prof-specialty", "Handlers-cleaners",
        "Machine-op-inspct", "Adm-clerical", "Farming-fishing",
        "Transport-moving", "Priv-house-serv", "Protective-serv", "Armed-Forces",
    ]),
    "race": sorted(["White", "Asian-Pac-Islander", "Amer-Indian-Eskimo", "Other", "Black"]),
    "sex": sorted(["Female", "Male"]),
}


def _encode_value(feature: str, value: Any) -> int:
    """Ordinally encode one categorical value; unknown values map to -1."""
    vocab = CATEGORIES[feature]
    try:
        return vocab.index(str(value).strip())
    except ValueError:
        return -1


def encode_frame(frame: pd.DataFrame) -> np.ndarray:
    """Encode a cleaned dataframe into the fixed FEATURE_ORDER float matrix."""
    columns = []
    for feature in FEATURE_ORDER:
        if feature in NUMERIC_FEATURES:
            columns.append(pd.to_numeric(frame[feature], errors="coerce").fillna(0).to_numpy(dtype=np.float32))
        else:
            encoded = frame[feature].map(lambda v, f=feature: _encode_value(f, v))
            columns.append(encoded.to_numpy(dtype=np.float32))
    return np.column_stack(columns).astype(np.float32)


def download(url: str, cache_dir: str) -> bytes:
    """Download a URL to a local cache and return its bytes (cached on reuse)."""
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, os.path.basename(url))
    if os.path.exists(cache_path):
        LOG.info("Using cached %s", cache_path)
        with open(cache_path, "rb") as handle:
            return handle.read()
    LOG.info("Downloading %s", url)
    request = urllib.request.Request(url, headers={"User-Agent": "nfcu-session-1-trainer/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310 (trusted UCI host)
        data = response.read()
    with open(cache_path, "wb") as handle:
        handle.write(data)
    LOG.info("Fetched %d bytes -> %s", len(data), cache_path)
    return data


def load_split(raw: bytes, skip_first_line: bool) -> pd.DataFrame:
    """Parse a raw UCI Adult split into a cleaned dataframe."""
    text = raw.decode("utf-8")
    if skip_first_line:
        # adult.test carries a non-data banner on line one.
        text = text.split("\n", 1)[1]
    frame = pd.read_csv(
        io.StringIO(text),
        header=None,
        names=COLUMNS,
        skipinitialspace=True,
        na_values="?",
        comment="|",
    )
    frame = frame.dropna(subset=COLUMNS).reset_index(drop=True)
    # adult.test labels carry a trailing period ("<=50K.").
    frame["income"] = frame["income"].str.replace(".", "", regex=False).str.strip()
    return frame


def build_inference_script() -> str:
    """Generate inference.py, embedding the shared encoder so it cannot drift."""
    categories_literal = json.dumps(CATEGORIES, indent=4, sort_keys=True)
    feature_order_literal = json.dumps(FEATURE_ORDER)
    numeric_literal = json.dumps(NUMERIC_FEATURES)
    return f'''# ABOUTME: SageMaker inference entrypoint for the UCI Adult income classifier.
# ABOUTME: Generated by train-sample-model.py; encodes features identically to training.
"""SageMaker XGBoost inference handlers for model-v{MODEL_VERSION}.

Implements the SageMaker model-serving contract: model_fn, input_fn, predict_fn,
output_fn. The feature encoder is identical to the one used at training time.
"""

import json
import os

import numpy as np
import xgboost as xgb

# The model file is named model.xgb but holds UBJSON; silence XGBoost's
# format-guess warning so serving output stays clean.
xgb.set_config(verbosity=0)

FEATURE_ORDER = {feature_order_literal}
NUMERIC_FEATURES = {numeric_literal}
CATEGORIES = {categories_literal}


def _encode_value(feature, value):
    """Ordinally encode one categorical value; unknown values map to -1."""
    vocab = CATEGORIES[feature]
    try:
        return vocab.index(str(value).strip())
    except ValueError:
        return -1


def _encode_record(record):
    """Encode one input record into the fixed FEATURE_ORDER float row."""
    row = []
    for feature in FEATURE_ORDER:
        value = record.get(feature)
        if feature in NUMERIC_FEATURES:
            row.append(float(value) if value is not None else 0.0)
        else:
            row.append(float(_encode_value(feature, value)))
    return row


def model_fn(model_dir):
    """Load the serialized booster from the SageMaker model directory."""
    booster = xgb.Booster()
    booster.load_model(os.path.join(model_dir, "model.xgb"))
    return booster


def input_fn(request_body, content_type="application/json"):
    """Parse a JSON request body into a list of input records."""
    if content_type != "application/json":
        raise ValueError(f"Unsupported content type: {{content_type}}")
    payload = json.loads(request_body)
    if isinstance(payload, dict):
        payload = [payload]
    return payload


def predict_fn(records, booster):
    """Run inference and return (income_over_50k, probability) per record."""
    matrix = xgb.DMatrix(np.asarray([_encode_record(r) for r in records], dtype=np.float32))
    probabilities = booster.predict(matrix)
    return [
        {{"income_over_50k": bool(p >= 0.5), "probability": float(p)}}
        for p in probabilities
    ]


def output_fn(prediction, accept="application/json"):
    """Serialize predictions as JSON (single object when one record was sent)."""
    body = prediction[0] if len(prediction) == 1 else prediction
    return json.dumps(body), accept
'''


def build_model_card() -> str:
    """Return the model card markdown (>= 100 bytes, names sensitive features)."""
    return f"""# Model Card: UCI Adult Income Classifier v{MODEL_VERSION}

## Overview
XGBoost binary classifier predicting whether a person's annual income exceeds
$50K, trained on the UCI Adult Census dataset (`uci-adult-2024-snapshot`). Built
as a teaching example for the NFCU Session 1 ML deployment pipeline webinar.

## Intended use
Demonstration of an end-to-end model deployment pipeline only: validation,
container signing, traceable deploys, and audit. It is **not** a production model.

## Inputs
Eight features: `age`, `hours_per_week` (numeric) and `workclass`, `education`,
`marital_status`, `occupation`, `race`, `sex` (categorical, ordinally encoded).

## Known limitations
This model includes `race`, `sex`, and `marital_status` as input features. A model
that conditions predictions on protected attributes is **not appropriate for
credit-risk modeling, lending, or any consequential decision about a person**. The
UCI Adult dataset reflects 1994 US census sampling and its documented societal
biases. It is used here strictly as a small, well-known binary classification
example to exercise deployment mechanics. The known biases are intentional and
left uncorrected so the pipeline's governance controls (model card review, audit
trail, approval gates) are the point of the demonstration — not model quality.
"""


def train_and_package(dry_run: bool, output_dir: str, cache_dir: str) -> str | None:
    """Download, train, evaluate, and (unless dry-run) package the artifact.

    Returns the artifact path, or None for a dry run.
    """
    os.environ.setdefault("PYTHONHASHSEED", "0")

    train_raw = download(TRAIN_URL, cache_dir)
    test_raw = download(TEST_URL, cache_dir)
    dataset_sha256 = hashlib.sha256(train_raw + test_raw).hexdigest()
    LOG.info("Dataset SHA256: %s", dataset_sha256)

    train_df = load_split(train_raw, skip_first_line=False)
    test_df = load_split(test_raw, skip_first_line=True)
    LOG.info("Loaded %d training rows, %d test rows", len(train_df), len(test_df))

    x_train = encode_frame(train_df)
    y_train = (train_df["income"].str.contains(">50K")).to_numpy(dtype=np.int32)
    x_test = encode_frame(test_df)
    y_test = (test_df["income"].str.contains(">50K")).to_numpy(dtype=np.int32)

    if dry_run:
        LOG.info("Dry run: download and preprocessing OK. Skipping training and artifact write.")
        return None

    classifier = xgb.XGBClassifier(
        max_depth=6,
        n_estimators=100,
        learning_rate=0.1,
        random_state=RANDOM_STATE,
        n_jobs=1,
        tree_method="hist",
        eval_metric="logloss",
    )
    classifier.fit(x_train, y_train)

    predictions = classifier.predict(x_test)
    accuracy = round(float(accuracy_score(y_test, predictions)), 2)
    f1 = round(float(f1_score(y_test, predictions)), 2)
    LOG.info("Evaluation: accuracy=%.2f f1=%.2f", accuracy, f1)

    # Serialize the booster to bytes deterministically. Save with an explicit .ubj
    # extension to select UBJSON (avoids a format-default warning); the bytes are
    # stored in the artifact as model.xgb and load_model sniffs the format on load.
    with tempfile.TemporaryDirectory() as tmp:
        model_path = os.path.join(tmp, "model.ubj")
        classifier.get_booster().save_model(model_path)
        with open(model_path, "rb") as handle:
            model_bytes = handle.read()

    build_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    training_run_id = f"train-{build_date}-{hashlib.sha256(model_bytes).hexdigest()[:8]}"

    signature = {
        "input": {
            "type": "object",
            "properties": {
                "age": {"type": "integer"},
                "workclass": {"type": "string"},
                "education": {"type": "string"},
                "marital_status": {"type": "string"},
                "occupation": {"type": "string"},
                "race": {"type": "string"},
                "sex": {"type": "string"},
                "hours_per_week": {"type": "integer"},
            },
            "required": ["age", "hours_per_week"],
        },
        "output": {
            "type": "object",
            "properties": {
                "income_over_50k": {"type": "boolean"},
                "probability": {"type": "number"},
            },
        },
    }
    metadata = {
        "model_name": "uci-adult-income-classifier",
        "model_version": MODEL_VERSION,
        "training_run_id": training_run_id,
        "training_dataset": DATASET_LABEL,
        "training_dataset_sha256": dataset_sha256,
        "hyperparameters": {"max_depth": 6, "n_estimators": 100, "learning_rate": 0.1},
        "evaluation": {"accuracy": accuracy, "f1_score": f1},
    }

    files = {
        f"{MODEL_DIR}/model.xgb": model_bytes,
        f"{MODEL_DIR}/inference.py": build_inference_script().encode("utf-8"),
        f"{MODEL_DIR}/signature.json": (json.dumps(signature, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        f"{MODEL_DIR}/metadata.json": (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        f"{MODEL_DIR}/model_card.md": build_model_card().encode("utf-8"),
    }

    artifact_path = os.path.join(output_dir, ARTIFACT_NAME)
    write_deterministic_tar(artifact_path, files)
    artifact_sha = hashlib.sha256(open(artifact_path, "rb").read()).hexdigest()
    LOG.info("Wrote %s (sha256=%s)", artifact_path, artifact_sha)
    return artifact_path


def write_deterministic_tar(out_path: str, files: dict[str, bytes]) -> None:
    """Write a gzip tarball with zeroed timestamps and fixed metadata.

    Sorting entry names and zeroing mtime/uid/gid/uname makes the output
    byte-identical across runs with identical file contents.
    """
    with open(out_path, "wb") as raw:
        gz = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
        try:
            tar = tarfile.open(fileobj=gz, mode="w")
            for name in sorted(files):
                data = files[name]
                info = tarfile.TarInfo(name=name)
                info.size = len(data)
                info.mtime = 0
                info.mode = 0o644
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                info.type = tarfile.REGTYPE
                tar.addfile(info, io.BytesIO(data))
            tar.close()
        finally:
            gz.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Train the UCI Adult sample model.")
    parser.add_argument("--dry-run", action="store_true", help="Download + preprocess only; write nothing.")
    parser.add_argument("--output-dir", default=".", help="Directory for the artifact tarball.")
    parser.add_argument(
        "--cache-dir",
        default=os.path.join(tempfile.gettempdir(), "nfcu-session-1-data"),
        help="Directory to cache the downloaded dataset.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    args = parse_args(argv)
    try:
        train_and_package(args.dry_run, args.output_dir, args.cache_dir)
    except Exception as exc:  # noqa: BLE001 - surface any failure with a clear message
        LOG.error("TRAINING FAILED: %s: %s", type(exc).__name__, exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
