# ABOUTME: drift-detector Lambda — per-feature PSI on recent traffic, every 2 min.
# ABOUTME: Emits DriftPSI metrics and (workshop shortcut) forces the drift alarm.
"""drift-detector.

Triggered by EventBridge every 2 minutes. Reads the last ``WINDOW_MINUTES`` of
prediction logs from the shadow-logs bucket and the captured reference
distribution from the baseline bucket, computes PSI for every feature, and emits
a ``DriftPSI`` CloudWatch metric (one datapoint per feature via the ``Feature``
dimension). If any feature's PSI exceeds the threshold it forces the drift alarm
to ALARM — see the workshop-only note in :func:`_force_alarm`.
"""

import io
import json
import logging
import os
from datetime import datetime, timedelta, timezone

import boto3
import pandas as pd

from psi import compute_psi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("drift-detector")

PSI_THRESHOLD = float(os.environ.get("PSI_THRESHOLD", "0.25"))
WINDOW_MINUTES = int(os.environ.get("WINDOW_MINUTES", "5"))
METRIC_NAMESPACE = os.environ.get("METRIC_NAMESPACE", "NFCU/Session3")


def _clients(region: str):
    """Build S3 and CloudWatch clients.

    Built per invocation rather than at module scope so the every-2-minute
    schedule always uses fresh credentials and so tests can drive them under a
    mocked AWS context.
    """
    return boto3.client("s3", region_name=region), boto3.client("cloudwatch", region_name=region)


def _read_reference(s3, bucket: str, key: str) -> pd.DataFrame:
    """Load the reference distribution parquet from S3."""
    body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    return pd.read_parquet(io.BytesIO(body))


def _read_current_window(s3, bucket: str, prefix: str, window_minutes: int) -> pd.DataFrame:
    """Read prediction-log records written within the last ``window_minutes``.

    Shadow logs are newline-delimited JSON, one prediction record per line. Object
    recency is judged by S3 ``LastModified``.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    paginator = s3.get_paginator("list_objects_v2")
    records: list[dict] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["LastModified"] < cutoff:
                continue
            body = s3.get_object(Bucket=bucket, Key=obj["Key"])["Body"].read().decode("utf-8")
            for line in body.splitlines():
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    return pd.DataFrame.from_records(records)


def _emit_metrics(cw, namespace: str, attendee_id: str, psi_by_feature: dict[str, float]) -> None:
    """Emit one DriftPSI datapoint per feature, dimensioned by feature + attendee."""
    metric_data = [
        {
            "MetricName": "DriftPSI",
            "Dimensions": [
                {"Name": "AttendeeId", "Value": attendee_id},
                {"Name": "Feature", "Value": feature},
            ],
            "Value": value,
            "Unit": "None",
        }
        for feature, value in psi_by_feature.items()
    ]
    # CloudWatch accepts up to 1000 datapoints per call; 8 features fit in one.
    cw.put_metric_data(Namespace=namespace, MetricData=metric_data)


def _force_alarm(cw, alarm_name: str, feature: str, value: float) -> None:
    """Force the drift alarm into ALARM for immediate visual feedback.

    WORKSHOP-ONLY SHORTCUT (design decision D3): production monitoring would let
    CloudWatch evaluate the threshold against the emitted DriftPSI datapoints on
    its own schedule. We call SetAlarmState directly so the alarm flips within the
    12-minute Lab 1 window instead of waiting for metric evaluation. Do not copy
    this into a real monitoring stack.
    """
    cw.set_alarm_state(
        AlarmName=alarm_name,
        StateValue="ALARM",
        StateReason=f"PSI {value:.3f} > {PSI_THRESHOLD} on feature '{feature}'",
    )


def handler(event, context):
    """EventBridge entry point. Returns the per-feature PSI map."""
    region = os.environ.get("AWS_REGION", "us-east-1")
    attendee_id = os.environ["ATTENDEE_ID"]
    shadow_bucket = os.environ.get("SHADOW_LOGS_BUCKET", f"workshop-lab-{attendee_id}-shadow-logs")
    shadow_prefix = os.environ.get("SHADOW_LOGS_PREFIX", "predictions/")
    baseline_bucket = os.environ.get("BASELINE_BUCKET", f"workshop-lab-{attendee_id}-baseline")
    reference_key = os.environ.get("REFERENCE_KEY", "reference.parquet")
    alarm_name = os.environ.get("DRIFT_ALARM_NAME", f"Drift-PSI-{attendee_id}")

    s3, cw = _clients(region)
    reference = _read_reference(s3, baseline_bucket, reference_key)
    current = _read_current_window(s3, shadow_bucket, shadow_prefix, WINDOW_MINUTES)

    if current.empty:
        logger.warning("No prediction records in the last %d minutes; nothing to score", WINDOW_MINUTES)
        return {"attendee_id": attendee_id, "psi": {}, "alarm": False}

    # Per feature (never aggregate) — only features present in both windows.
    features = [f for f in reference.columns if f in current.columns]
    psi_by_feature = {f: compute_psi(reference[f], current[f]) for f in features}
    logger.info("PSI by feature: %s", {f: round(v, 4) for f, v in psi_by_feature.items()})

    _emit_metrics(cw, METRIC_NAMESPACE, attendee_id, psi_by_feature)

    drifting = {f: v for f, v in psi_by_feature.items() if v > PSI_THRESHOLD}
    alarm_fired = False
    if drifting:
        worst_feature = max(drifting, key=drifting.get)
        _force_alarm(cw, alarm_name, worst_feature, drifting[worst_feature])
        alarm_fired = True
        logger.info("Drift alarm forced ALARM on '%s' (PSI=%.3f)", worst_feature, drifting[worst_feature])

    return {"attendee_id": attendee_id, "psi": psi_by_feature, "alarm": alarm_fired}
