# ABOUTME: drift-simulator Lambda — sends drifted traffic to the SageMaker endpoint.
# ABOUTME: Shifts hours_per_week by +Normal(15,5) and sends 10 req/s for 5 minutes.
"""drift-simulator.

Manually invoked in Lab 2. Samples clean feature rows, shifts the
``hours_per_week`` feature by ``+ Normal(15, 5)`` clipped to ``[0, 100]`` (design
decision D9), and sends them to the production endpoint at 10 req/s for 5 minutes.
The drift-detector (running every 2 min on a 5-min window) should see PSI on
``hours_per_week`` cross 0.25 within 4–6 minutes.
"""

import io
import logging
import os
import time

import boto3
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("drift-simulator")

# The eight lab features, in the order the model's CSV input expects.
FEATURE_ORDER = [
    "age", "workclass", "education_num", "marital_status",
    "occupation", "race", "sex", "hours_per_week",
]
DRIFT_FEATURE = "hours_per_week"
DRIFT_MEAN = 15.0
DRIFT_SD = 5.0
CLIP_MIN, CLIP_MAX = 0.0, 100.0
DEFAULT_RATE = 10      # requests per second
DEFAULT_DURATION = 300  # seconds (5 minutes)


def apply_drift(df: pd.DataFrame, seed: int | None = None) -> pd.DataFrame:
    """Shift ``hours_per_week`` by ``+ Normal(15, 5)`` clipped to [0, 100].

    All other columns are returned unchanged.
    """
    rng = np.random.default_rng(seed)
    out = df.copy()
    shift = rng.normal(DRIFT_MEAN, DRIFT_SD, size=len(out))
    out[DRIFT_FEATURE] = (out[DRIFT_FEATURE].to_numpy(dtype=float) + shift).clip(CLIP_MIN, CLIP_MAX)
    return out


def _to_csv_row(row: dict) -> str:
    """Serialize one record to a CSV line in FEATURE_ORDER (no label)."""
    return ",".join(str(row[f]) for f in FEATURE_ORDER)


def _load_samples(s3, bucket: str, key: str, n: int) -> pd.DataFrame:
    """Load the clean feature sample (reference.parquet) from the baseline bucket."""
    body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    df = pd.read_parquet(io.BytesIO(body))[FEATURE_ORDER]
    if len(df) > n:
        df = df.sample(n=n, random_state=0).reset_index(drop=True)
    return df


def _make_invoker(runtime, endpoint_name: str):
    """Return a callable that sends one CSV payload to the SageMaker endpoint."""
    def invoke(body: str):
        return runtime.invoke_endpoint(
            EndpointName=endpoint_name, ContentType="text/csv", Body=body.encode("utf-8")
        )
    return invoke


def send_traffic(invoke, rows: list[dict], rate_per_s: int, duration_s: int, sleep=None) -> int:
    """Send ``rate_per_s * duration_s`` requests, cycling through ``rows``.

    Args:
        invoke: Callable taking a CSV payload string (one request).
        rows: Drifted records to cycle through.
        rate_per_s: Target requests per second.
        duration_s: Total duration in seconds.
        sleep: Pacing function; defaults to the module ``time.sleep`` looked up at
            call time (so tests can monkeypatch ``handler.time.sleep``).

    Returns:
        The number of requests sent.
    """
    pace = sleep if sleep is not None else time.sleep
    target = rate_per_s * duration_s
    interval = 1.0 / rate_per_s if rate_per_s > 0 else 0.0
    sent = 0
    for i in range(target):
        invoke(_to_csv_row(rows[i % len(rows)]))
        sent += 1
        pace(interval)
        if sent % 500 == 0:
            logger.info("sent %d/%d requests", sent, target)
    return sent


def handler(event, context):
    """Manual entry point. Event may override ``rate`` and ``duration_s``."""
    region = os.environ.get("AWS_REGION", "us-east-1")
    attendee_id = os.environ["ATTENDEE_ID"]
    endpoint_name = os.environ.get("ENDPOINT_NAME", f"workshop-lab-{attendee_id}-production")
    baseline_bucket = os.environ.get("BASELINE_BUCKET", f"workshop-lab-{attendee_id}-baseline")
    reference_key = os.environ.get("REFERENCE_KEY", "reference.parquet")
    rate = int(event.get("rate", DEFAULT_RATE)) if isinstance(event, dict) else DEFAULT_RATE
    duration_s = int(event.get("duration_s", DEFAULT_DURATION)) if isinstance(event, dict) else DEFAULT_DURATION

    s3 = boto3.client("s3", region_name=region)
    runtime = boto3.client("sagemaker-runtime", region_name=region)

    samples = _load_samples(s3, baseline_bucket, reference_key, n=1000)
    drifted = apply_drift(samples)
    rows = drifted.to_dict(orient="records")

    invoke = _make_invoker(runtime, endpoint_name)
    logger.info("Sending %d req/s for %ds to %s", rate, duration_s, endpoint_name)
    sent = send_traffic(invoke, rows, rate, duration_s)

    return {
        "attendee_id": attendee_id,
        "endpoint": endpoint_name,
        "drifted_feature": DRIFT_FEATURE,
        "requests_sent": sent,
    }
