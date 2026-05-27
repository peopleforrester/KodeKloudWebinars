# ABOUTME: Tests for the evidently-runner Lambda: 0.7.x API compliance + S3 flow.
# ABOUTME: Stubs the (container-only) evidently package to drive the upload path.
import io
import json
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

boto3 = pytest.importorskip("boto3")
pytest.importorskip("moto")
from moto import mock_aws  # noqa: E402

REGION = "us-east-1"
ATTENDEE = "lab-007"
BASELINE_BUCKET = f"workshop-lab-{ATTENDEE}-baseline"
SHADOW_BUCKET = f"workshop-lab-{ATTENDEE}-shadow-logs"
REPORTS_BUCKET = f"workshop-lab-{ATTENDEE}-drift-reports"

HANDLER_SRC = Path(__file__).resolve().parent.parent / "lambdas/evidently-runner/handler.py"

FEATURES = ["age", "workclass", "education_num", "marital_status",
            "occupation", "race", "sex", "hours_per_week"]


def _frame(n=500, hours_mean=40):
    rng = np.random.default_rng(3)
    return pd.DataFrame({
        "age": rng.integers(18, 80, n),
        "workclass": rng.choice(["Private", "Gov"], n),
        "education_num": rng.integers(1, 16, n),
        "marital_status": rng.choice(["Married", "Single"], n),
        "occupation": rng.choice(["Tech", "Sales"], n),
        "race": rng.choice(["A", "B"], n),
        "sex": rng.choice(["Male", "Female"], n),
        "hours_per_week": rng.normal(hours_mean, 8, n).clip(1, 99),
    })


def _install_fake_evidently(monkeypatch):
    """Register a minimal stub for the container-only evidently package."""
    ev = types.ModuleType("evidently")

    class DataDefinition:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class Dataset:
        def __init__(self, df, data_definition=None):
            self.df = df

        @classmethod
        def from_pandas(cls, df, data_definition=None):
            return cls(df, data_definition)

    class _Eval:
        def save_html(self, path):
            Path(path).write_text("<html><body>drift report: hours_per_week</body></html>")

    class Report:
        def __init__(self, metrics):
            self.metrics = metrics

        def run(self, current, reference):
            assert isinstance(current, Dataset) and isinstance(reference, Dataset)
            return _Eval()

    ev.Dataset, ev.DataDefinition, ev.Report = Dataset, DataDefinition, Report

    presets = types.ModuleType("evidently.presets")
    presets.DataDriftPreset = type("DataDriftPreset", (), {})
    presets.DataQualityPreset = type("DataQualityPreset", (), {})

    monkeypatch.setitem(sys.modules, "evidently", ev)
    monkeypatch.setitem(sys.modules, "evidently.presets", presets)


def test_handler_uses_0_7_api_and_no_column_mapping():
    src = HANDLER_SRC.read_text()
    assert "Report([DataDriftPreset(), DataQualityPreset()])" in src
    assert "data_definition=" in src
    assert "Dataset.from_pandas" in src
    assert "column_mapping" not in src  # legacy 0.4.x arg must be absent


@mock_aws
def test_handler_uploads_report_and_returns_signed_url(import_lambda, monkeypatch):
    s3 = boto3.client("s3", region_name=REGION)
    for bucket in (BASELINE_BUCKET, SHADOW_BUCKET, REPORTS_BUCKET):
        s3.create_bucket(Bucket=bucket)

    buf = io.BytesIO()
    _frame(hours_mean=40).to_parquet(buf, index=False)
    s3.put_object(Bucket=BASELINE_BUCKET, Key="reference.parquet", Body=buf.getvalue())

    current = _frame(hours_mean=70)  # drifted
    body = "\n".join(json.dumps(r) for r in current.to_dict(orient="records"))
    s3.put_object(Bucket=SHADOW_BUCKET, Key="predictions/win.jsonl", Body=body.encode())

    _install_fake_evidently(monkeypatch)
    for k, v in {
        "ATTENDEE_ID": ATTENDEE, "AWS_REGION": REGION,
        "BASELINE_BUCKET": BASELINE_BUCKET, "SHADOW_LOGS_BUCKET": SHADOW_BUCKET,
        "DRIFT_REPORTS_BUCKET": REPORTS_BUCKET,
    }.items():
        monkeypatch.setenv(k, v)

    handler = import_lambda("evidently-runner", "handler")
    result = handler.handler({}, None)

    assert result["expires_in"] == 3600
    assert result["report_key"].endswith(".html")
    assert result["report_url"].startswith("https://")
    # Signed URL carries expiry/signature query params.
    assert "Expires" in result["report_url"] or "X-Amz-Expires" in result["report_url"]

    # The HTML object actually landed in the drift-reports bucket.
    obj = s3.get_object(Bucket=REPORTS_BUCKET, Key=result["report_key"])
    assert obj["ContentType"] == "text/html"
    assert b"drift report" in obj["Body"].read()
