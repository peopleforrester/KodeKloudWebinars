# ABOUTME: Tests for the nannyml-runner Lambda: CBPE wiring, delta, metric emission.
# ABOUTME: Stubs the (container-only) nannyml package to drive the S3/CloudWatch path.
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
NAMESPACE = "NFCU/Session3"
HANDLER_SRC = Path(__file__).resolve().parent.parent / "lambdas/nannyml-runner/handler.py"


def _preds(n, proba_mean, with_label):
    """A prediction-log frame. Stub CBPE derives 'AUC' from y_pred_proba.mean()."""
    rng = np.random.default_rng(11)
    proba = np.clip(rng.normal(proba_mean, 0.02, n), 0, 1)
    frame = {"y_pred_proba": proba, "y_pred": (proba > 0.5).astype(int)}
    if with_label:
        frame["income"] = rng.integers(0, 2, n)
    return pd.DataFrame(frame)


def _install_fake_nannyml(monkeypatch):
    """Stub nannyml.CBPE: 'estimated AUC' = mean(y_pred_proba) of the window."""
    nml = types.ModuleType("nannyml")

    class _Results:
        def __init__(self, value):
            self._value = value

        def filter(self, period=None):
            return self

        def to_df(self):
            cols = pd.MultiIndex.from_tuples([("roc_auc", "value")])
            return pd.DataFrame([[self._value]], columns=cols)

    class CBPE:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.proba_col = kwargs["y_pred_proba"]

        def fit(self, reference_df):
            return self

        def estimate(self, frame):
            return _Results(float(frame[self.proba_col].mean()))

    nml.CBPE = CBPE
    monkeypatch.setitem(sys.modules, "nannyml", nml)


def test_handler_uses_cbpe_binary_api():
    src = HANDLER_SRC.read_text()
    assert "nml.CBPE(" in src
    assert "problem_type=\"classification_binary\"" in src
    assert "metrics=[\"roc_auc\"]" in src
    for key in ("estimated_auc_reference", "estimated_auc_current", "delta"):
        assert key in src


@mock_aws
def test_handler_returns_auc_delta_and_emits_metric(import_lambda, monkeypatch):
    s3 = boto3.client("s3", region_name=REGION)
    cw = boto3.client("cloudwatch", region_name=REGION)
    s3.create_bucket(Bucket=BASELINE_BUCKET)
    s3.create_bucket(Bucket=SHADOW_BUCKET)

    # Reference (labelled): higher mean proba -> higher stub AUC (0.85).
    buf = io.BytesIO()
    _preds(2000, proba_mean=0.85, with_label=True).to_parquet(buf, index=False)
    s3.put_object(Bucket=BASELINE_BUCKET, Key="reference_predictions.parquet", Body=buf.getvalue())

    # Current (unlabelled): lower mean proba -> lower stub AUC (0.80) -> negative delta.
    current = _preds(2000, proba_mean=0.80, with_label=False)
    body = "\n".join(json.dumps(r) for r in current.to_dict(orient="records"))
    s3.put_object(Bucket=SHADOW_BUCKET, Key="predictions/win.jsonl", Body=body.encode())

    _install_fake_nannyml(monkeypatch)
    for k, v in {
        "ATTENDEE_ID": ATTENDEE, "AWS_REGION": REGION,
        "BASELINE_BUCKET": BASELINE_BUCKET, "SHADOW_LOGS_BUCKET": SHADOW_BUCKET,
    }.items():
        monkeypatch.setenv(k, v)

    handler = import_lambda("nannyml-runner", "handler")
    result = handler.handler({}, None)

    assert set(result) >= {"estimated_auc_reference", "estimated_auc_current", "delta"}
    assert result["estimated_auc_reference"] == pytest.approx(0.85, abs=0.02)
    assert result["estimated_auc_current"] == pytest.approx(0.80, abs=0.02)
    assert result["delta"] == pytest.approx(
        result["estimated_auc_current"] - result["estimated_auc_reference"], abs=1e-9)

    names = {m["MetricName"] for m in cw.list_metrics(Namespace=NAMESPACE)["Metrics"]}
    assert {"EstimatedAUC", "EstimatedAUCDelta"} <= names
