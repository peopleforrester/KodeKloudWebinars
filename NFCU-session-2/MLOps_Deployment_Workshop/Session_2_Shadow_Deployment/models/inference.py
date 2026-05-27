# ABOUTME: SageMaker inference entry point bundled into each model tar.gz.
# ABOUTME: Loads the joblib pipeline and returns label + positive-class probability.
# SPDX-License-Identifier: Apache-2.0
"""SageMaker SKLearn container inference handlers.

The SageMaker scikit-learn serving container imports the functions below from
``code/inference.py`` inside the model tarball. The model artifact is the
joblib pipeline produced by the trainers, stored at ``model.joblib``.
"""

from __future__ import annotations

import json
import os
from typing import Any

import joblib
import pandas as pd

CONTENT_TYPE_JSON = "application/json"


def model_fn(model_dir: str) -> Any:
    """Load the joblib pipeline from the model directory.

    Args:
        model_dir: Directory SageMaker extracts the model tarball into.

    Returns:
        The fitted scikit-learn pipeline.
    """
    return joblib.load(os.path.join(model_dir, "model.joblib"))


def input_fn(request_body: str, request_content_type: str) -> pd.DataFrame:
    """Deserialize a JSON request into a single-row DataFrame.

    Args:
        request_body: Raw request payload.
        request_content_type: MIME type; only JSON is supported.

    Returns:
        A one-row DataFrame of features.

    Raises:
        ValueError: If the content type is not JSON.
    """
    if request_content_type != CONTENT_TYPE_JSON:
        raise ValueError(f"Unsupported content type: {request_content_type}")
    payload = json.loads(request_body)
    records = payload if isinstance(payload, list) else [payload]
    return pd.DataFrame.from_records(records)


def predict_fn(input_data: pd.DataFrame, model: Any) -> list[dict[str, Any]]:
    """Run inference and return label plus positive-class probability.

    Args:
        input_data: Feature rows produced by ``input_fn``.
        model: The pipeline returned by ``model_fn``.

    Returns:
        One result dict per input row.
    """
    labels = model.predict(input_data)
    probabilities = model.predict_proba(input_data)[:, 1]
    return [
        {"prediction": int(label), "probability": float(prob)}
        for label, prob in zip(labels, probabilities, strict=True)
    ]


def output_fn(prediction: list[dict[str, Any]], accept: str) -> str:
    """Serialize predictions to JSON.

    Args:
        prediction: Output of ``predict_fn``.
        accept: Requested response MIME type.

    Returns:
        JSON-encoded predictions.
    """
    return json.dumps(prediction)
