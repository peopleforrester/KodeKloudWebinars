# ABOUTME: Integration test for the drift-detector Lambda against mocked AWS.
# ABOUTME: Confirms per-feature metric emission and the drift-alarm transition.
import io
import json
import os

import numpy as np
import pandas as pd
import pytest

boto3 = pytest.importorskip("boto3")
moto = pytest.importorskip("moto")
from moto import mock_aws  # noqa: E402

REGION = "us-east-1"
ATTENDEE = "lab-007"
BASELINE_BUCKET = f"workshop-lab-{ATTENDEE}-baseline"
SHADOW_BUCKET = f"workshop-lab-{ATTENDEE}-shadow-logs"
ALARM_NAME = f"Drift-PSI-{ATTENDEE}"
NAMESPACE = "NFCU/Session3"

FEATURES = ["age", "workclass", "education_num", "marital_status",
            "occupation", "race", "sex", "hours_per_week"]


def _reference_frame(n: int = 4000) -> pd.DataFrame:
    rng = np.random.default_rng(123)
    return pd.DataFrame({
        "age": rng.normal(40, 12, n).clip(17, 90),
        "workclass": rng.choice(["Private", "Self-emp", "Gov"], n, p=[0.7, 0.2, 0.1]),
        "education_num": rng.integers(1, 16, n),
        "marital_status": rng.choice(["Married", "Single"], n, p=[0.5, 0.5]),
        "occupation": rng.choice(["Tech", "Sales", "Admin"], n, p=[0.4, 0.3, 0.3]),
        "race": rng.choice(["A", "B", "C"], n, p=[0.6, 0.3, 0.1]),
        "sex": rng.choice(["Male", "Female"], n, p=[0.5, 0.5]),
        "hours_per_week": rng.normal(40, 8, n).clip(1, 99),
    })


def _current_records(n: int = 2000) -> list[dict]:
    """Same as reference except hours_per_week is shifted hard (drift)."""
    rng = np.random.default_rng(999)
    base = _reference_frame(n)
    base["hours_per_week"] = rng.normal(70, 8, n).clip(1, 99)  # +30 mean shift
    return base.to_dict(orient="records")


@mock_aws
def test_drift_detector_emits_metrics_and_fires_alarm(import_lambda, monkeypatch):
    s3 = boto3.client("s3", region_name=REGION)
    cw = boto3.client("cloudwatch", region_name=REGION)
    s3.create_bucket(Bucket=BASELINE_BUCKET)
    s3.create_bucket(Bucket=SHADOW_BUCKET)

    # Upload reference parquet.
    buf = io.BytesIO()
    _reference_frame().to_parquet(buf, index=False)
    s3.put_object(Bucket=BASELINE_BUCKET, Key="reference.parquet", Body=buf.getvalue())

    # Upload current window as newline-delimited JSON prediction logs.
    body = "\n".join(json.dumps(r) for r in _current_records())
    s3.put_object(Bucket=SHADOW_BUCKET, Key="predictions/window.jsonl", Body=body.encode())

    # The drift alarm must exist for SetAlarmState to target it.
    cw.put_metric_alarm(
        AlarmName=ALARM_NAME, Namespace=NAMESPACE, MetricName="DriftPSI",
        Statistic="Maximum", Period=120, EvaluationPeriods=1,
        Threshold=0.25, ComparisonOperator="GreaterThanThreshold",
        Dimensions=[{"Name": "AttendeeId", "Value": ATTENDEE}],
    )

    for key, value in {
        "ATTENDEE_ID": ATTENDEE, "AWS_REGION": REGION,
        "BASELINE_BUCKET": BASELINE_BUCKET, "SHADOW_LOGS_BUCKET": SHADOW_BUCKET,
        "DRIFT_ALARM_NAME": ALARM_NAME,
    }.items():
        monkeypatch.setenv(key, value)

    handler = import_lambda("drift-detector", "handler")
    result = handler.handler({}, None)

    # Alarm fired, and it was hours_per_week that drifted.
    assert result["alarm"] is True
    assert result["psi"]["hours_per_week"] > 0.25
    for feature in ["age", "education_num", "marital_status", "sex", "race"]:
        assert result["psi"][feature] < 0.1

    # One DriftPSI metric per feature (per-feature, not aggregate).
    metrics = cw.list_metrics(Namespace=NAMESPACE, MetricName="DriftPSI")["Metrics"]
    emitted_features = {
        d["Value"] for m in metrics for d in m["Dimensions"] if d["Name"] == "Feature"
    }
    assert emitted_features == set(FEATURES)

    # Alarm is in ALARM state.
    alarms = cw.describe_alarms(AlarmNames=[ALARM_NAME])["MetricAlarms"]
    assert alarms[0]["StateValue"] == "ALARM"
    assert "hours_per_week" in alarms[0]["StateReason"]


@mock_aws
def test_drift_detector_no_traffic_is_noop(import_lambda, monkeypatch):
    s3 = boto3.client("s3", region_name=REGION)
    s3.create_bucket(Bucket=BASELINE_BUCKET)
    s3.create_bucket(Bucket=SHADOW_BUCKET)
    buf = io.BytesIO()
    _reference_frame().to_parquet(buf, index=False)
    s3.put_object(Bucket=BASELINE_BUCKET, Key="reference.parquet", Body=buf.getvalue())

    for key, value in {
        "ATTENDEE_ID": ATTENDEE, "AWS_REGION": REGION,
        "BASELINE_BUCKET": BASELINE_BUCKET, "SHADOW_LOGS_BUCKET": SHADOW_BUCKET,
        "DRIFT_ALARM_NAME": ALARM_NAME,
    }.items():
        monkeypatch.setenv(key, value)

    handler = import_lambda("drift-detector", "handler")
    result = handler.handler({}, None)
    assert result["alarm"] is False
    assert result["psi"] == {}
