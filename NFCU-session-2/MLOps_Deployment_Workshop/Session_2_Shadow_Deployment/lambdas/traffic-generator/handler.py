# ABOUTME: Manual traffic generator — sends synthetic UCI Adult requests to shadow-mirror.
# ABOUTME: Biases ~15% of samples toward the pre-identified champion/challenger disagreement region.
# SPDX-License-Identifier: Apache-2.0
"""Traffic-generator Lambda.

Invoked manually with ``{"duration_minutes": N, "rate": M}``. Reads the UCI Adult
test split and the disagreement-region row IDs from S3, then drives requests at
``rate`` requests/second for ``duration_minutes`` against the shadow-mirror API
Gateway URL, biasing ~15% of samples toward the disagreement region.
"""

from __future__ import annotations

import json
import logging
import os
import random
import time
import urllib.request
from typing import Any

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SHADOW_MIRROR_URL_ENV = "SHADOW_MIRROR_URL"
TEST_DATA_URI_ENV = "TEST_DATA_URI"
DISAGREEMENT_URI_ENV = "DISAGREEMENT_REGION_URI"
DISAGREEMENT_BIAS = 0.15


def get_s3_client() -> Any:
    """Return an S3 client (indirected for testability)."""
    return boto3.client("s3")


def _parse_s3_uri(uri: str) -> tuple[str, str]:
    """Split an ``s3://bucket/key`` URI into ``(bucket, key)``."""
    without = uri.removeprefix("s3://")
    bucket, _, key = without.partition("/")
    return bucket, key


def _load_json(s3: Any, uri: str) -> Any:
    """Load and parse a JSON object from S3."""
    bucket, key = _parse_s3_uri(uri)
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj["Body"].read().decode("utf-8"))


def send_request(url: str, payload: dict[str, Any]) -> float:
    """POST a JSON payload to the shadow-mirror URL and return latency in ms.

    Args:
        url: Shadow-mirror API Gateway URL.
        payload: Feature record to score.

    Returns:
        Round-trip latency in milliseconds.

    Raises:
        urllib.error.HTTPError: On a non-2xx response (e.g. 5xx).
    """
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(  # noqa: S310 — fixed https API Gateway URL
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    start = time.perf_counter()
    with urllib.request.urlopen(request) as response:  # noqa: S310
        response.read()
    return (time.perf_counter() - start) * 1000.0


def choose_row(
    rows: list[dict[str, Any]],
    disagreement_indices: list[int],
    rng: random.Random,
    bias: float = DISAGREEMENT_BIAS,
) -> dict[str, Any]:
    """Pick a row, biasing toward the disagreement region with probability ``bias``."""
    if disagreement_indices and rng.random() < bias:
        idx = rng.choice(disagreement_indices)
        if 0 <= idx < len(rows):
            return rows[idx]
    return rng.choice(rows)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Drive synthetic traffic at the requested rate and duration.

    Args:
        event: ``{"duration_minutes": N, "rate": M, "seed": optional int}``.
        context: Lambda context (unused).

    Returns:
        Summary ``{"requests_sent", "failures", "average_latency_ms"}``.
    """
    duration_minutes = float(event.get("duration_minutes", 1))
    rate = float(event.get("rate", 1))
    rng = random.Random(event.get("seed"))

    url = os.environ[SHADOW_MIRROR_URL_ENV]
    s3 = get_s3_client()
    rows = _load_json(s3, os.environ[TEST_DATA_URI_ENV])
    disagreement = _load_json(s3, os.environ[DISAGREEMENT_URI_ENV])
    disagreement_indices = disagreement.get("disagreement_row_indices", [])

    total = int(round(rate * duration_minutes * 60))
    interval = 1.0 / rate if rate > 0 else 0.0

    sent = 0
    failures = 0
    latencies: list[float] = []
    for _ in range(total):
        row = choose_row(rows, disagreement_indices, rng)
        try:
            latencies.append(send_request(url, row))
        except Exception:  # noqa: BLE001 — count 5xx/transport errors, keep going
            failures += 1
            logger.warning("request failed", exc_info=True)
        sent += 1
        if interval:
            time.sleep(interval)

    average_latency = sum(latencies) / len(latencies) if latencies else 0.0
    summary = {
        "requests_sent": sent,
        "failures": failures,
        "average_latency_ms": round(average_latency, 3),
    }
    logger.info("traffic complete: %s", summary)
    return summary
