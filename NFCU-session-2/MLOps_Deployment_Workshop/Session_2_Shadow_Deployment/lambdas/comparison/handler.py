# ABOUTME: Scheduled comparison Lambda — joins champion/challenger shadow logs,
# ABOUTME: computes agreement/latency/disparate-impact, evaluates promotion criteria.
# SPDX-License-Identifier: Apache-2.0
"""Comparison Lambda.

Runs on a 5-minute EventBridge schedule. Reads shadow-log entries written by the
shadow-mirror Lambda, joins each with its challenger async output via
``request_id``, computes comparison metrics, emits CloudWatch custom metrics,
and writes a comparison result (with a promotion verdict) to S3.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict

import boto3
import yaml
from criteria import evaluate_criteria

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SHADOW_LOG_BUCKET_ENV = "SHADOW_LOG_BUCKET"
RESULTS_BUCKET_ENV = "COMPARISON_RESULTS_BUCKET"
CRITERIA_PATH_ENV = "PROMOTION_CRITERIA_PATH"
NAMESPACE = "Workshop/Session2"


class JoinedRecord(TypedDict):
    """A champion/challenger pair joined on request_id."""

    champion_label: int
    challenger_label: int
    champion_latency_ms: float
    challenger_latency_ms: float
    sex: str
    race: str


def get_s3_client() -> Any:
    """Return an S3 client (indirected for testability)."""
    return boto3.client("s3")


def get_cloudwatch_client() -> Any:
    """Return a CloudWatch client (indirected for testability)."""
    return boto3.client("cloudwatch")


def _percentile(values: list[float], pct: float) -> float:
    """Return the ``pct`` percentile of ``values`` using nearest-rank."""
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(0, min(len(ordered) - 1, round(pct / 100.0 * (len(ordered) - 1))))
    return float(ordered[rank])


def _positive_rates(records: list[JoinedRecord], key: str) -> dict[str, float]:
    """Predicted-positive rate per protected group for the given model label."""
    groups: dict[str, list[int]] = {}
    for record in records:
        group = f"{record['sex']}|{record['race']}"
        groups.setdefault(group, []).append(int(record[key]))  # type: ignore[literal-required]
    return {group: sum(labels) / len(labels) for group, labels in groups.items()}


def _ratios(rates: dict[str, float]) -> dict[str, float]:
    """Group selection-rate ratios relative to the highest-rate group."""
    if not rates:
        return {}
    top = max(rates.values())
    if top == 0:
        return {group: 1.0 for group in rates}
    return {group: rate / top for group, rate in rates.items()}


def compute_metrics(records: list[JoinedRecord]) -> dict[str, Any]:
    """Compute comparison metrics from joined champion/challenger records.

    Args:
        records: Joined records produced by :func:`join_records`.

    Returns:
        A metrics mapping consumed by the promotion-criteria evaluator and the
        CloudWatch emitter.
    """
    n = len(records)
    agreement = (
        sum(1 for r in records if r["champion_label"] == r["challenger_label"]) / n if n else 0.0
    )
    champ_p95 = _percentile([r["champion_latency_ms"] for r in records], 95)
    chal_p95 = _percentile([r["challenger_latency_ms"] for r in records], 95)
    delta_pct = ((chal_p95 - champ_p95) / champ_p95 * 100.0) if champ_p95 else 0.0

    champion_rates = _positive_rates(records, "champion_label")
    challenger_rates = _positive_rates(records, "challenger_label")
    champion_ratios = _ratios(champion_rates)
    challenger_ratios = _ratios(challenger_rates)

    per_group: dict[str, int] = {}
    for record in records:
        group = f"{record['sex']}|{record['race']}"
        per_group[group] = per_group.get(group, 0) + 1

    return {
        "agreement_rate": round(agreement, 4),
        "n_observations": n,
        "latency_p95_champion_ms": round(champ_p95, 3),
        "latency_p95_challenger_ms": round(chal_p95, 3),
        "latency_p95_delta_pct": round(delta_pct, 3),
        "observations_per_protected_group": per_group,
        "predicted_positive_rate": {
            "champion": champion_rates,
            "challenger": challenger_rates,
        },
        "disparate_impact": {
            "champion": champion_ratios,
            "challenger": challenger_ratios,
            "min_ratio_champion": min(champion_ratios.values()) if champion_ratios else 1.0,
            "min_ratio_challenger": (min(challenger_ratios.values()) if challenger_ratios else 1.0),
        },
    }


def _first_record(payload: Any) -> dict[str, Any]:
    """Return the first prediction dict from an inference response."""
    if isinstance(payload, list):
        return payload[0] if payload else {}
    return payload if isinstance(payload, dict) else {}


def join_records(
    s3: Any, shadow_log_bucket: str, entries: list[dict[str, Any]]
) -> tuple[list[JoinedRecord], list[str]]:
    """Join shadow-log entries with their challenger async outputs.

    Args:
        s3: S3 client.
        shadow_log_bucket: Bucket holding async challenger outputs.
        entries: Parsed shadow-log entries.

    Returns:
        Tuple of (joined records, deferred request_ids whose challenger output
        is not yet available).
    """
    joined: list[JoinedRecord] = []
    deferred: list[str] = []
    for entry in entries:
        uri = entry.get("challenger_async_output_uri")
        challenger = _load_challenger_output(s3, uri) if uri else None
        if challenger is None:
            deferred.append(entry["request_id"])
            continue
        champion = _first_record(entry.get("champion_response"))
        challenger_pred = _first_record(challenger)
        payload = entry.get("input_payload", {})
        joined.append(
            {
                "champion_label": int(champion.get("prediction", 0)),
                "challenger_label": int(challenger_pred.get("prediction", 0)),
                "champion_latency_ms": float(champion.get("latency_ms", 0.0)),
                "challenger_latency_ms": float(challenger_pred.get("latency_ms", 0.0)),
                "sex": str(payload.get("sex", "unknown")),
                "race": str(payload.get("race", "unknown")),
            }
        )
    return joined, deferred


def _parse_s3_uri(uri: str) -> tuple[str, str]:
    """Split an ``s3://bucket/key`` URI into ``(bucket, key)``."""
    without = uri.removeprefix("s3://")
    bucket, _, key = without.partition("/")
    return bucket, key


def _load_challenger_output(s3: Any, uri: str) -> Any | None:
    """Load a challenger async output JSON; return ``None`` if absent."""
    bucket, key = _parse_s3_uri(uri)
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
    except Exception:  # noqa: BLE001 — missing output means not yet available
        return None
    return json.loads(obj["Body"].read().decode("utf-8"))


def _load_shadow_entries(s3: Any, bucket: str, watermark: str) -> list[dict[str, Any]]:
    """Load shadow-log entries newer than ``watermark`` (ISO timestamp)."""
    entries: list[dict[str, Any]] = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix="raw/"):
        for item in page.get("Contents", []):
            obj = s3.get_object(Bucket=bucket, Key=item["Key"])
            entry = json.loads(obj["Body"].read().decode("utf-8"))
            if entry.get("timestamp", "") > watermark:
                entries.append(entry)
    return entries


def _read_watermark(s3: Any, results_bucket: str) -> str:
    """Read the last-processed timestamp watermark, or epoch if unset."""
    try:
        obj = s3.get_object(Bucket=results_bucket, Key="state/watermark.json")
    except Exception:  # noqa: BLE001
        return "1970-01-01T00:00:00+00:00"
    return str(json.loads(obj["Body"].read().decode("utf-8")).get("watermark"))


def _emit_metrics(cw: Any, metrics: dict[str, Any]) -> None:
    """Emit the shadow comparison custom metrics to CloudWatch."""
    data: list[dict[str, Any]] = [
        {"MetricName": "ShadowAgreementRate", "Value": metrics["agreement_rate"], "Unit": "None"},
        {
            "MetricName": "ShadowLatencyP95Delta",
            "Value": metrics["latency_p95_delta_pct"],
            "Unit": "Percent",
        },
    ]
    for group, ratio in metrics["disparate_impact"]["challenger"].items():
        data.append(
            {
                "MetricName": "ShadowDisparateImpactRatio",
                "Dimensions": [{"Name": "ProtectedGroup", "Value": group}],
                "Value": ratio,
                "Unit": "None",
            }
        )
    cw.put_metric_data(Namespace=NAMESPACE, MetricData=data)


def _load_criteria() -> dict[str, Any]:
    """Load the promotion-criteria YAML bundled alongside the Lambda."""
    path = os.environ.get(
        CRITERIA_PATH_ENV, str(Path(__file__).resolve().parent / "promotion-criteria.yaml")
    )
    with open(path) as fh:
        criteria: dict[str, Any] = yaml.safe_load(fh)
    return criteria


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """EventBridge entry point: run one comparison pass.

    Args:
        event: EventBridge scheduled event (unused).
        context: Lambda context (unused).

    Returns:
        The comparison result written to S3.
    """
    shadow_bucket = os.environ[SHADOW_LOG_BUCKET_ENV]
    results_bucket = os.environ[RESULTS_BUCKET_ENV]
    s3 = get_s3_client()

    watermark = _read_watermark(s3, results_bucket)
    entries = _load_shadow_entries(s3, shadow_bucket, watermark)
    joined, deferred = join_records(s3, shadow_bucket, entries)

    metrics = compute_metrics(joined)
    criteria = _load_criteria()
    verdict = evaluate_criteria(metrics, criteria)

    timestamps = [e["timestamp"] for e in entries if "timestamp" in e]
    result = {
        "metrics": metrics,
        "criteria_evaluated": verdict["criteria_evaluated"],
        "promotion_check_status": verdict["promotion_check_status"],
        "failure_reasons": verdict["failure_reasons"],
        "evaluation_window_start": min(timestamps) if timestamps else watermark,
        "evaluation_window_end": max(timestamps) if timestamps else watermark,
        "deferred_request_ids": deferred,
    }

    now = datetime.now(UTC).isoformat()
    body = json.dumps(result, indent=2).encode("utf-8")
    s3.put_object(Bucket=results_bucket, Key="latest.json", Body=body)
    s3.put_object(Bucket=results_bucket, Key=f"archive/{now}.json", Body=body)
    if timestamps:
        s3.put_object(
            Bucket=results_bucket,
            Key="state/watermark.json",
            Body=json.dumps({"watermark": max(timestamps)}).encode("utf-8"),
        )

    _emit_metrics(get_cloudwatch_client(), metrics)
    logger.info(
        "comparison complete: status=%s observations=%d deferred=%d",
        verdict["promotion_check_status"],
        metrics["n_observations"],
        len(deferred),
    )
    return result
