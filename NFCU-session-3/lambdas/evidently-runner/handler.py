# ABOUTME: evidently-runner Lambda — generates an Evidently drift report on demand.
# ABOUTME: Uses the Evidently 0.7.x API and returns a 1-hour signed URL to the HTML.
"""evidently-runner.

Manually invoked in Lab 3 Part 1. Reads the reference distribution and the last
hour of production traffic, builds an Evidently drift + data-quality report using
the **0.7.x API**, renders it to HTML, uploads it to the drift-reports bucket, and
returns a signed URL (1-hour expiry).

0.7.x API note (design decision D1): the modern API wraps data in
``Dataset.from_pandas(df, data_definition=DataDefinition(...))`` and builds
``Report([DataDriftPreset(), DataQualityPreset()])``. The legacy per-column
mapping constructor argument from the 0.4.x API is NOT used.
"""

import io
import json
import logging
import os
from datetime import datetime, timedelta, timezone

import boto3
import pandas as pd

from evidently import Dataset, DataDefinition, Report
from evidently.presets import DataDriftPreset, DataQualityPreset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evidently-runner")

NUMERIC_FEATURES = ["age", "education_num", "hours_per_week"]
CATEGORICAL_FEATURES = ["workclass", "marital_status", "occupation", "race", "sex"]
WINDOW_MINUTES = int(os.environ.get("CURRENT_WINDOW_MINUTES", "60"))
URL_EXPIRY_SECONDS = 3600  # 1 hour


def _read_parquet(s3, bucket: str, key: str) -> pd.DataFrame:
    body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    return pd.read_parquet(io.BytesIO(body))


def _read_current_window(s3, bucket: str, prefix: str, minutes: int) -> pd.DataFrame:
    """Read prediction-log records from the last ``minutes`` (newline JSON)."""
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


def _as_dataset(df: pd.DataFrame) -> "Dataset":
    """Wrap a DataFrame as an Evidently Dataset with an explicit DataDefinition."""
    data_definition = DataDefinition(
        numerical_columns=NUMERIC_FEATURES,
        categorical_columns=CATEGORICAL_FEATURES,
    )
    return Dataset.from_pandas(df, data_definition=data_definition)


def build_report(current: pd.DataFrame, reference: pd.DataFrame, html_path: str) -> None:
    """Build and render the Evidently report to ``html_path`` (0.7.x API)."""
    current_ds = _as_dataset(current)
    reference_ds = _as_dataset(reference)
    report = Report([DataDriftPreset(), DataQualityPreset()])
    my_eval = report.run(current_ds, reference_ds)
    my_eval.save_html(html_path)


def handler(event, context):
    """Manual entry point. Returns the signed report URL."""
    region = os.environ.get("AWS_REGION", "us-east-1")
    attendee_id = os.environ["ATTENDEE_ID"]
    baseline_bucket = os.environ.get("BASELINE_BUCKET", f"workshop-lab-{attendee_id}-baseline")
    reports_bucket = os.environ.get("DRIFT_REPORTS_BUCKET", f"workshop-lab-{attendee_id}-drift-reports")
    shadow_bucket = os.environ.get("SHADOW_LOGS_BUCKET", f"workshop-lab-{attendee_id}-shadow-logs")
    shadow_prefix = os.environ.get("SHADOW_LOGS_PREFIX", "predictions/")
    reference_key = os.environ.get("REFERENCE_KEY", "reference.parquet")

    s3 = boto3.client("s3", region_name=region)
    reference = _read_parquet(s3, baseline_bucket, reference_key)
    current = _read_current_window(s3, shadow_bucket, shadow_prefix, WINDOW_MINUTES)
    if current.empty:
        raise RuntimeError("No prediction records in the current window; cannot build a report.")

    # Compare on the shared feature columns only.
    features = [c for c in reference.columns if c in current.columns]
    html_path = "/tmp/evidently_report.html"
    logger.info("Building Evidently report on %d features (%d current rows)", len(features), len(current))
    build_report(current[features], reference[features], html_path)

    key = f"reports/{attendee_id}/{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.html"
    with open(html_path, "rb") as fh:
        s3.put_object(Bucket=reports_bucket, Key=key, Body=fh.read(), ContentType="text/html")

    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": reports_bucket, "Key": key},
        ExpiresIn=URL_EXPIRY_SECONDS,
    )
    logger.info("Report uploaded to s3://%s/%s", reports_bucket, key)
    return {"attendee_id": attendee_id, "report_key": key, "report_url": url,
            "expires_in": URL_EXPIRY_SECONDS}
