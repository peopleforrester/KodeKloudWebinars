# ABOUTME: nannyml-runner Lambda — ground-truth-free performance estimation (CBPE).
# ABOUTME: Estimates ROC-AUC on reference vs current windows and reports the delta.
"""nannyml-runner.

Manually invoked in Lab 3 Part 2. Uses NannyML's Confidence-Based Performance
Estimation (CBPE) to estimate ROC-AUC on a production window **without ground
truth labels** — the core lesson: you can monitor output quality even when labels
are not yet available.

CBPE fits on a labelled reference window (predicted probabilities + predicted
class + true class), then estimates ROC-AUC on unlabelled windows from the
predicted probabilities alone. The handler estimates on both the reference and the
current window and reports the delta.
"""

import io
import json
import logging
import os
from datetime import datetime, timedelta, timezone

import boto3
import pandas as pd

import nannyml as nml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nannyml-runner")

# Prediction-log column names (UCI Adult: <=50K vs >50K).
Y_PRED_PROBA = os.environ.get("Y_PRED_PROBA_COL", "y_pred_proba")
Y_PRED = os.environ.get("Y_PRED_COL", "y_pred")
Y_TRUE = os.environ.get("Y_TRUE_COL", "income")
WINDOW_MINUTES = int(os.environ.get("CURRENT_WINDOW_MINUTES", "60"))
CHUNK_SIZE = int(os.environ.get("CBPE_CHUNK_SIZE", "1000"))
METRIC_NAMESPACE = os.environ.get("METRIC_NAMESPACE", "NFCU/Session3")


def _read_parquet(s3, bucket: str, key: str) -> pd.DataFrame:
    body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    return pd.read_parquet(io.BytesIO(body))


def _read_current_window(s3, bucket: str, prefix: str, minutes: int) -> pd.DataFrame:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    paginator = s3.get_paginator("list_objects_v2")
    records: list[dict] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["LastModified"] < cutoff:
                continue
            text = s3.get_object(Bucket=bucket, Key=obj["Key"])["Body"].read().decode("utf-8")
            records.extend(json.loads(line) for line in text.splitlines() if line.strip())
    return pd.DataFrame.from_records(records)


def _build_estimator():
    """Construct the CBPE estimator for binary classification."""
    return nml.CBPE(
        y_pred_proba=Y_PRED_PROBA,
        y_pred=Y_PRED,
        y_true=Y_TRUE,
        metrics=["roc_auc"],
        chunk_size=CHUNK_SIZE,
        problem_type="classification_binary",
    )


def _mean_estimated_auc(results) -> float:
    """Extract the mean estimated ROC-AUC from a CBPE results object.

    NannyML returns a (possibly MultiIndex) DataFrame; the estimated value lives
    under the ``roc_auc`` metric's ``value`` column. Access is defensive across
    NannyML layout variations.
    """
    df = results.filter(period="analysis").to_df()
    # MultiIndex columns: ('roc_auc', 'value')
    if isinstance(df.columns, pd.MultiIndex):
        for top in ("roc_auc",):
            if (top, "value") in df.columns:
                return float(df[(top, "value")].mean())
    # Flat columns: "roc_auc value" or similar.
    for col in df.columns:
        name = col if isinstance(col, str) else " ".join(map(str, col))
        if "roc_auc" in name and "value" in name:
            return float(df[col].mean())
    raise KeyError(f"Could not locate roc_auc value column in CBPE results: {list(df.columns)}")


def estimate_auc(estimator, frame: pd.DataFrame) -> float:
    """Estimate mean ROC-AUC on a single window."""
    return _mean_estimated_auc(estimator.estimate(frame))


def _emit_metrics(cw, attendee_id: str, auc_current: float, delta: float) -> None:
    cw.put_metric_data(
        Namespace=METRIC_NAMESPACE,
        MetricData=[
            {"MetricName": "EstimatedAUC",
             "Dimensions": [{"Name": "AttendeeId", "Value": attendee_id}],
             "Value": auc_current, "Unit": "None"},
            {"MetricName": "EstimatedAUCDelta",
             "Dimensions": [{"Name": "AttendeeId", "Value": attendee_id}],
             "Value": delta, "Unit": "None"},
        ],
    )


def handler(event, context):
    """Manual entry point. Returns reference/current AUC estimates and the delta."""
    region = os.environ.get("AWS_REGION", "us-east-1")
    attendee_id = os.environ["ATTENDEE_ID"]
    baseline_bucket = os.environ.get("BASELINE_BUCKET", f"workshop-lab-{attendee_id}-baseline")
    shadow_bucket = os.environ.get("SHADOW_LOGS_BUCKET", f"workshop-lab-{attendee_id}-shadow-logs")
    shadow_prefix = os.environ.get("SHADOW_LOGS_PREFIX", "predictions/")
    reference_key = os.environ.get("REFERENCE_PREDICTIONS_KEY", "reference_predictions.parquet")

    s3 = boto3.client("s3", region_name=region)
    cw = boto3.client("cloudwatch", region_name=region)

    reference = _read_parquet(s3, baseline_bucket, reference_key)
    current = _read_current_window(s3, shadow_bucket, shadow_prefix, WINDOW_MINUTES)
    if current.empty:
        raise RuntimeError("No prediction records in the current window; cannot estimate performance.")

    estimator = _build_estimator()
    estimator.fit(reference)
    auc_reference = estimate_auc(estimator, reference)
    auc_current = estimate_auc(estimator, current)
    delta = auc_current - auc_reference

    _emit_metrics(cw, attendee_id, auc_current, delta)
    logger.info("Estimated ROC-AUC reference=%.4f current=%.4f delta=%.4f",
                auc_reference, auc_current, delta)

    return {
        "attendee_id": attendee_id,
        "estimated_auc_reference": auc_reference,
        "estimated_auc_current": auc_current,
        "delta": delta,
    }
