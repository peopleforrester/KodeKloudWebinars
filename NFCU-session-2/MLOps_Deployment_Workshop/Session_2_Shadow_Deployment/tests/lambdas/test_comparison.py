# ABOUTME: Unit tests for the comparison Lambda: metric math, criteria gate, S3 run.
# ABOUTME: Covers all promotion pass/fail combinations with deterministic fixtures.
# SPDX-License-Identifier: Apache-2.0
"""Tests for the comparison handler and the shared criteria evaluator."""

from __future__ import annotations

import json
from types import ModuleType
from typing import Any

import boto3
import pytest
from moto import mock_aws

SHADOW_BUCKET = "workshop-lab-alice-shadow-logs"
RESULTS_BUCKET = "workshop-lab-alice-comparison-results"


def _base_metrics(**overrides: Any) -> dict[str, Any]:
    """A metrics dict that passes every criterion unless overridden."""
    metrics: dict[str, Any] = {
        "agreement_rate": 0.92,
        "n_observations": 1500,
        "latency_p95_champion_ms": 140.0,
        "latency_p95_challenger_ms": 150.0,
        "latency_p95_delta_pct": 7.1,
        "observations_per_protected_group": {"Male|White": 800, "Female|Black": 700},
        "disparate_impact": {"min_ratio_challenger": 0.86, "min_ratio_champion": 0.82},
    }
    metrics.update(overrides)
    return metrics


def test_criteria_met(comparison: ModuleType, promotion_criteria: dict[str, Any]) -> None:
    verdict = comparison.evaluate_criteria(_base_metrics(), promotion_criteria)
    assert verdict["promotion_check_status"] == "ready"
    assert verdict["failure_reasons"] == []


def test_agreement_too_low(comparison: ModuleType, promotion_criteria: dict[str, Any]) -> None:
    verdict = comparison.evaluate_criteria(_base_metrics(agreement_rate=0.82), promotion_criteria)
    assert verdict["promotion_check_status"] == "not_ready"
    assert any("below minimum" in r for r in verdict["failure_reasons"])


def test_agreement_too_high(comparison: ModuleType, promotion_criteria: dict[str, Any]) -> None:
    verdict = comparison.evaluate_criteria(_base_metrics(agreement_rate=0.995), promotion_criteria)
    assert verdict["promotion_check_status"] == "not_ready"
    assert any("exceeds maximum 0.99" in r for r in verdict["failure_reasons"])


def test_disparate_impact_violation(
    comparison: ModuleType, promotion_criteria: dict[str, Any]
) -> None:
    metrics = _base_metrics(
        disparate_impact={"min_ratio_challenger": 0.70, "min_ratio_champion": 0.82}
    )
    verdict = comparison.evaluate_criteria(metrics, promotion_criteria)
    assert verdict["promotion_check_status"] == "not_ready"
    assert any("below required" in r for r in verdict["failure_reasons"])


def test_insufficient_observations(
    comparison: ModuleType, promotion_criteria: dict[str, Any]
) -> None:
    verdict = comparison.evaluate_criteria(_base_metrics(n_observations=500), promotion_criteria)
    assert verdict["promotion_check_status"] == "not_ready"
    assert any("500 observations, minimum 1000 required" in r for r in verdict["failure_reasons"])


def test_insufficient_per_group_observations(
    comparison: ModuleType, promotion_criteria: dict[str, Any]
) -> None:
    metrics = _base_metrics(
        observations_per_protected_group={"Male|White": 800, "Female|Black": 40}
    )
    verdict = comparison.evaluate_criteria(metrics, promotion_criteria)
    assert verdict["promotion_check_status"] == "not_ready"
    assert any("smallest protected group" in r for r in verdict["failure_reasons"])


def test_disparate_impact_ratio_math(comparison: ModuleType) -> None:
    # Four groups, challenger positive rates [0.50, 0.45, 0.42, 0.35] -> ratios
    # relative to 0.50 of [1.00, 0.90, 0.84, 0.70]. Use 100 rows per group with
    # the right number of positives, champion identical for simplicity.
    rates = {"g0": 0.50, "g1": 0.45, "g2": 0.42, "g3": 0.35}
    records: list[dict[str, Any]] = []
    for group, rate in rates.items():
        positives = round(rate * 100)
        for i in range(100):
            label = 1 if i < positives else 0
            records.append(
                {
                    "champion_label": label,
                    "challenger_label": label,
                    "champion_latency_ms": 100.0,
                    "challenger_latency_ms": 110.0,
                    "sex": group,
                    "race": "X",
                }
            )
    metrics = comparison.compute_metrics(records)
    ratios = metrics["disparate_impact"]["challenger"]
    assert round(ratios["g0|X"], 2) == 1.00
    assert round(ratios["g1|X"], 2) == 0.90
    assert round(ratios["g2|X"], 2) == 0.84
    assert round(ratios["g3|X"], 2) == 0.70
    assert metrics["agreement_rate"] == 1.0
    assert metrics["latency_p95_delta_pct"] == 10.0


@mock_aws
def test_handler_writes_result(comparison: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    from pathlib import Path

    criteria_path = Path(__file__).resolve().parents[2] / "config" / "promotion-criteria.yaml"
    monkeypatch.setenv("SHADOW_LOG_BUCKET", SHADOW_BUCKET)
    monkeypatch.setenv("COMPARISON_RESULTS_BUCKET", RESULTS_BUCKET)
    monkeypatch.setenv("PROMOTION_CRITERIA_PATH", str(criteria_path))

    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=SHADOW_BUCKET)
    s3.create_bucket(Bucket=RESULTS_BUCKET)

    # One joined pair: champion and challenger agree.
    output_uri = f"s3://{SHADOW_BUCKET}/async-output/req-1.out"
    s3.put_object(
        Bucket=SHADOW_BUCKET,
        Key="async-output/req-1.out",
        Body=json.dumps([{"prediction": 1, "probability": 0.8, "latency_ms": 30.0}]).encode(),
    )
    s3.put_object(
        Bucket=SHADOW_BUCKET,
        Key="raw/year=2026/month=06/day=04/req-1.json",
        Body=json.dumps(
            {
                "timestamp": "2026-06-04T10:00:00+00:00",
                "request_id": "req-1",
                "input_payload": {"sex": "Male", "race": "White"},
                "champion_response": [{"prediction": 1, "probability": 0.7, "latency_ms": 25.0}],
                "challenger_async_output_uri": output_uri,
            }
        ).encode(),
    )

    result = comparison.handler({}, None)
    assert result["metrics"]["n_observations"] == 1
    assert result["metrics"]["agreement_rate"] == 1.0
    # 1 observation is below minimum_observations -> not ready.
    assert result["promotion_check_status"] == "not_ready"

    latest = json.loads(s3.get_object(Bucket=RESULTS_BUCKET, Key="latest.json")["Body"].read())
    assert latest["evaluation_window_start"] == "2026-06-04T10:00:00+00:00"


@mock_aws
def test_handler_defers_unjoinable(comparison: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    from pathlib import Path

    criteria_path = Path(__file__).resolve().parents[2] / "config" / "promotion-criteria.yaml"
    monkeypatch.setenv("SHADOW_LOG_BUCKET", SHADOW_BUCKET)
    monkeypatch.setenv("COMPARISON_RESULTS_BUCKET", RESULTS_BUCKET)
    monkeypatch.setenv("PROMOTION_CRITERIA_PATH", str(criteria_path))

    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=SHADOW_BUCKET)
    s3.create_bucket(Bucket=RESULTS_BUCKET)
    # Challenger output does not exist yet -> the entry is deferred.
    s3.put_object(
        Bucket=SHADOW_BUCKET,
        Key="raw/year=2026/month=06/day=04/req-2.json",
        Body=json.dumps(
            {
                "timestamp": "2026-06-04T10:05:00+00:00",
                "request_id": "req-2",
                "input_payload": {"sex": "Female", "race": "Black"},
                "champion_response": [{"prediction": 0, "probability": 0.2, "latency_ms": 25.0}],
                "challenger_async_output_uri": f"s3://{SHADOW_BUCKET}/async-output/missing.out",
            }
        ).encode(),
    )

    result = comparison.handler({}, None)
    assert result["deferred_request_ids"] == ["req-2"]
    assert result["metrics"]["n_observations"] == 0
