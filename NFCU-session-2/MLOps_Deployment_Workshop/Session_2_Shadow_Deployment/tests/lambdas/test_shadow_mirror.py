# ABOUTME: Unit tests for the shadow-mirror Lambda using moto (S3) and a fake SageMaker.
# ABOUTME: Covers the happy path, challenger failure isolation, and malformed input.
# SPDX-License-Identifier: Apache-2.0
"""Tests for the shadow-mirror fan-out handler."""

from __future__ import annotations

import json
from types import ModuleType
from typing import Any

import boto3
import pytest
from moto import mock_aws

BUCKET = "workshop-lab-alice-shadow-logs"


class _FakeBody:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data


class _FakeSageMaker:
    """Stand-in for the SageMaker runtime client (moto does not mock it)."""

    def __init__(self, *, fail_async: bool = False) -> None:
        self.fail_async = fail_async
        self.sync_calls: list[str] = []
        self.async_calls: list[str] = []

    def invoke_endpoint(
        self, *, EndpointName: str, ContentType: str, Body: bytes
    ) -> dict[str, Any]:
        self.sync_calls.append(EndpointName)
        payload = [{"prediction": 1, "probability": 0.91, "latency_ms": 12.3}]
        return {"Body": _FakeBody(json.dumps(payload).encode("utf-8"))}

    def invoke_endpoint_async(
        self, *, EndpointName: str, ContentType: str, InputLocation: str, InferenceId: str
    ) -> dict[str, Any]:
        self.async_calls.append(EndpointName)
        if self.fail_async:
            raise RuntimeError("challenger endpoint unavailable")
        return {"OutputLocation": f"s3://{BUCKET}/async-output/{InferenceId}.out"}


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHAMPION_ENDPOINT_ARN", "workshop-lab-alice-production")
    monkeypatch.setenv("CHALLENGER_ENDPOINT_ARN", "workshop-lab-alice-challenger")
    monkeypatch.setenv("SHADOW_LOG_BUCKET", BUCKET)


@mock_aws
def test_happy_path_returns_champion_and_logs(
    shadow_mirror: ModuleType, env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)
    fake = _FakeSageMaker()
    monkeypatch.setattr(shadow_mirror, "get_sagemaker_runtime", lambda: fake)

    response = shadow_mirror.handler(
        {"body": json.dumps({"sex": "Male", "race": "White", "age": 39})}, None
    )

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["endpoint_source"] == "champion"
    assert body["request_id"]
    assert body["prediction"] == [{"prediction": 1, "probability": 0.91, "latency_ms": 12.3}]
    assert fake.sync_calls == ["workshop-lab-alice-production"]
    assert fake.async_calls == ["workshop-lab-alice-challenger"]

    logs = s3.list_objects_v2(Bucket=BUCKET, Prefix="raw/")
    assert logs["KeyCount"] == 1
    entry = json.loads(s3.get_object(Bucket=BUCKET, Key=logs["Contents"][0]["Key"])["Body"].read())
    assert entry["request_id"] == body["request_id"]
    assert entry["challenger_async_output_uri"].startswith(f"s3://{BUCKET}/async-output/")


@mock_aws
def test_challenger_failure_never_breaks_caller(
    shadow_mirror: ModuleType, env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)
    fake = _FakeSageMaker(fail_async=True)
    monkeypatch.setattr(shadow_mirror, "get_sagemaker_runtime", lambda: fake)

    response = shadow_mirror.handler({"body": json.dumps({"sex": "Female", "race": "Black"})}, None)

    assert response["statusCode"] == 200
    logs = s3.list_objects_v2(Bucket=BUCKET, Prefix="raw/")
    entry = json.loads(s3.get_object(Bucket=BUCKET, Key=logs["Contents"][0]["Key"])["Body"].read())
    assert entry["challenger_async_output_uri"] is None


@mock_aws
def test_malformed_body_returns_400(
    shadow_mirror: ModuleType, env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(shadow_mirror, "get_sagemaker_runtime", lambda: _FakeSageMaker())
    response = shadow_mirror.handler({"body": "{not valid json"}, None)
    assert response["statusCode"] == 400
    assert json.loads(response["body"])["error"] == "invalid JSON body"


def test_endpoint_name_extracts_from_arn(shadow_mirror: ModuleType) -> None:
    arn = "arn:aws:sagemaker:us-east-1:123456789012:endpoint/workshop-lab-alice-challenger"
    assert shadow_mirror._endpoint_name(arn) == "workshop-lab-alice-challenger"
    assert shadow_mirror._endpoint_name("plain-name") == "plain-name"
