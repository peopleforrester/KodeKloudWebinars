# ABOUTME: API Gateway shadow-mirror Lambda — champion sync, challenger async.
# ABOUTME: The challenger can never affect the caller-visible response (zero member impact).
# SPDX-License-Identifier: Apache-2.0
"""Shadow-mirror fan-out handler.

Invokes the champion endpoint synchronously and returns only its response to the
caller, while mirroring the same request to the challenger endpoint
asynchronously. A failing or slow challenger cannot affect the caller. Every
request is correlated by a UUID ``request_id`` written into the shadow log so
the comparison Lambda can later join champion and challenger outputs.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import UTC, datetime
from typing import Any

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CHAMPION_ENV = "CHAMPION_ENDPOINT_ARN"
CHALLENGER_ENV = "CHALLENGER_ENDPOINT_ARN"
SHADOW_LOG_BUCKET_ENV = "SHADOW_LOG_BUCKET"
CONTENT_TYPE = "application/json"


def get_sagemaker_runtime() -> Any:
    """Return a SageMaker runtime client (indirected for testability)."""
    return boto3.client("sagemaker-runtime")


def get_s3_client() -> Any:
    """Return an S3 client (indirected for testability)."""
    return boto3.client("s3")


def _endpoint_name(value: str) -> str:
    """Extract the endpoint name from an ARN, or return the value unchanged.

    The promotion workflow swaps the ``*_ENDPOINT_ARN`` environment variables.
    SageMaker's runtime API takes an endpoint *name*, so accept either form.
    """
    marker = ":endpoint/"
    if marker in value:
        return value.split(marker, 1)[1]
    return value


def _shadow_log_key(request_id: str, now: datetime) -> str:
    """Return the partitioned S3 key for a shadow-log entry."""
    return f"raw/year={now.year:04d}/month={now.month:02d}/day={now.day:02d}/{request_id}.json"


def _invoke_challenger_async(
    *, endpoint: str, bucket: str, request_id: str, body: str
) -> str | None:
    """Invoke the challenger asynchronously; never raise to the caller.

    Uploads the request body to S3 (async inputs must be in S3), calls
    ``invoke_endpoint_async``, and returns the async output URI. On any failure
    it logs and returns ``None`` so the caller is unaffected.
    """
    try:
        s3 = get_s3_client()
        input_key = f"async-input/{request_id}.json"
        s3.put_object(Bucket=bucket, Key=input_key, Body=body.encode("utf-8"))
        response = get_sagemaker_runtime().invoke_endpoint_async(
            EndpointName=endpoint,
            ContentType=CONTENT_TYPE,
            InputLocation=f"s3://{bucket}/{input_key}",
            InferenceId=request_id,
        )
        return str(response.get("OutputLocation"))
    except Exception:  # noqa: BLE001 — challenger must never break the caller
        logger.exception("Challenger async invocation failed for request_id=%s", request_id)
        return None


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """API Gateway proxy entry point.

    Args:
        event: API Gateway proxy event with a JSON ``body``.
        context: Lambda context (unused).

    Returns:
        An API Gateway proxy response containing the champion's prediction,
        ``endpoint_source: "champion"``, and the correlation ``request_id``.
    """
    champion = _endpoint_name(os.environ[CHAMPION_ENV])
    challenger = _endpoint_name(os.environ[CHALLENGER_ENV])
    bucket = os.environ[SHADOW_LOG_BUCKET_ENV]

    request_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    raw_body = event.get("body") or "{}"

    # Validate the request body up front and fail explicitly on malformed input.
    try:
        parsed_input = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
    except json.JSONDecodeError:
        logger.warning("Rejected malformed request body for request_id=%s", request_id)
        return {
            "statusCode": 400,
            "headers": {"Content-Type": CONTENT_TYPE},
            "body": json.dumps({"error": "invalid JSON body", "request_id": request_id}),
        }
    body = json.dumps(parsed_input)

    # Champion: synchronous, caller-visible.
    champion_raw = get_sagemaker_runtime().invoke_endpoint(
        EndpointName=champion,
        ContentType=CONTENT_TYPE,
        Body=body.encode("utf-8"),
    )
    champion_response = json.loads(champion_raw["Body"].read().decode("utf-8"))

    # Challenger: asynchronous, never caller-visible.
    challenger_output_uri = _invoke_challenger_async(
        endpoint=challenger, bucket=bucket, request_id=request_id, body=body
    )

    # Shadow-log entry for offline comparison.
    log_entry = {
        "timestamp": now.isoformat(),
        "request_id": request_id,
        "input_payload": parsed_input,
        "champion_response": champion_response,
        "challenger_async_output_uri": challenger_output_uri,
    }
    get_s3_client().put_object(
        Bucket=bucket,
        Key=_shadow_log_key(request_id, now),
        Body=json.dumps(log_entry).encode("utf-8"),
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": CONTENT_TYPE},
        "body": json.dumps(
            {
                "prediction": champion_response,
                "endpoint_source": "champion",
                "request_id": request_id,
            }
        ),
    }
