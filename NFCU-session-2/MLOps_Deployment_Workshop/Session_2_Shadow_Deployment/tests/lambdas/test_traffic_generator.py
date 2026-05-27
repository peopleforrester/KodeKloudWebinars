# ABOUTME: Unit tests for the traffic-generator Lambda (rate, bias, 5xx handling).
# ABOUTME: Mocks the HTTP sender and uses moto for the S3 test-data reads.
# SPDX-License-Identifier: Apache-2.0
"""Tests for the traffic-generator handler."""

from __future__ import annotations

import json
import random
from types import ModuleType
from typing import Any

import boto3
import pytest
from moto import mock_aws

BUCKET = "workshop-lab-alice-shadow-logs"
ROWS = [{"sex": "Male", "race": "White", "age": 30 + i} for i in range(10)]
DISAGREEMENT = {"disagreement_row_indices": [0, 1, 2]}


def _seed_s3() -> None:
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)
    s3.put_object(Bucket=BUCKET, Key="test-data.json", Body=json.dumps(ROWS).encode())
    s3.put_object(Bucket=BUCKET, Key="disagreement.json", Body=json.dumps(DISAGREEMENT).encode())


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHADOW_MIRROR_URL", "https://example.test/predict")
    monkeypatch.setenv("TEST_DATA_URI", f"s3://{BUCKET}/test-data.json")
    monkeypatch.setenv("DISAGREEMENT_REGION_URI", f"s3://{BUCKET}/disagreement.json")


@mock_aws
def test_sends_expected_request_count(
    traffic_generator: ModuleType, env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_s3()
    sent: list[dict[str, Any]] = []
    monkeypatch.setattr(
        traffic_generator, "send_request", lambda url, payload: sent.append(payload) or 12.0
    )
    monkeypatch.setattr(traffic_generator.time, "sleep", lambda _seconds: None)

    summary = traffic_generator.handler({"duration_minutes": 0.5, "rate": 2, "seed": 1}, None)

    assert summary["requests_sent"] == 60  # 2 req/s * 30s
    assert summary["failures"] == 0
    assert summary["average_latency_ms"] == 12.0
    assert len(sent) == 60


@mock_aws
def test_counts_failures_without_aborting(
    traffic_generator: ModuleType, env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_s3()
    calls = {"n": 0}

    def flaky(url: str, payload: dict[str, Any]) -> float:
        calls["n"] += 1
        if calls["n"] % 2 == 0:
            raise RuntimeError("HTTP 503")
        return 10.0

    monkeypatch.setattr(traffic_generator, "send_request", flaky)
    monkeypatch.setattr(traffic_generator.time, "sleep", lambda _seconds: None)

    summary = traffic_generator.handler({"duration_minutes": 0.1, "rate": 1, "seed": 1}, None)

    assert summary["requests_sent"] == 6
    assert summary["failures"] == 3


def test_choose_row_bias(traffic_generator: ModuleType) -> None:
    rng = random.Random(0)
    # bias=1.0 always selects from the disagreement region.
    for _ in range(50):
        row = traffic_generator.choose_row(
            ROWS, DISAGREEMENT["disagreement_row_indices"], rng, bias=1.0
        )
        assert row in [ROWS[i] for i in DISAGREEMENT["disagreement_row_indices"]]


def test_choose_row_no_bias_uses_full_set(traffic_generator: ModuleType) -> None:
    rng = random.Random(0)
    picked = {
        traffic_generator.choose_row(ROWS, DISAGREEMENT["disagreement_row_indices"], rng, bias=0.0)[
            "age"
        ]
        for _ in range(200)
    }
    # With no bias and 200 draws over 10 rows, we expect coverage beyond the
    # three disagreement rows.
    assert len(picked) > 3
