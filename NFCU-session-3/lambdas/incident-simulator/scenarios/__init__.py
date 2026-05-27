# ABOUTME: Shared context and helpers for the five incident-simulator scenarios.
# ABOUTME: Each scenario module exposes NAME, EXPECTED_ALARM, trigger(), cleanup().
"""Incident scenario framework.

Every scenario module exposes a uniform interface so the handler can dispatch by
number:

* ``NAME`` — human-readable scenario name.
* ``EXPECTED_ALARM`` — the alarm an attendee should expect (or ``None``).
* ``CLEANUP_AFTER_MINUTES`` — auto-cleanup horizon (15 per the spec).
* ``trigger(ctx)`` — start the incident; returns a metadata dict.
* ``cleanup(ctx)`` — revert all side effects; returns a metadata dict.

All AWS access goes through :class:`IncidentContext` so scenarios are testable
with stub clients and leave no persistent state once ``cleanup`` runs.
"""

from dataclasses import dataclass, field
from typing import Any

CLEANUP_AFTER_MINUTES = 15
CONTROL_PREFIX = "incident-control/"


@dataclass
class IncidentContext:
    """Carries config and (injectable) AWS clients for a scenario."""

    attendee_id: str
    endpoint_name: str
    region: str = "us-east-1"
    control_bucket: str = ""
    sagemaker: Any = None          # boto3 "sagemaker" client
    runtime: Any = None            # boto3 "sagemaker-runtime" client
    s3: Any = None                 # boto3 "s3" client
    lambda_client: Any = None      # boto3 "lambda" client
    config: dict = field(default_factory=dict)

    def alarm(self, base: str) -> str:
        return f"{base}-{self.attendee_id}"


# The eight lab features, model CSV input order (mirrors the simulators).
FEATURE_ORDER = [
    "age", "workclass", "education_num", "marital_status",
    "occupation", "race", "sex", "hours_per_week",
]


def write_marker(ctx: IncidentContext, scenario_key: str, payload: dict) -> str:
    """Record an incident-control marker in S3 so cleanup is idempotent."""
    import json

    key = f"{CONTROL_PREFIX}{scenario_key}.json"
    if ctx.s3 and ctx.control_bucket:
        ctx.s3.put_object(
            Bucket=ctx.control_bucket, Key=key,
            Body=json.dumps(payload).encode("utf-8"), ContentType="application/json",
        )
    return key


def clear_marker(ctx: IncidentContext, scenario_key: str) -> bool:
    """Delete the incident-control marker if present. Returns True if cleared."""
    key = f"{CONTROL_PREFIX}{scenario_key}.json"
    if ctx.s3 and ctx.control_bucket:
        ctx.s3.delete_object(Bucket=ctx.control_bucket, Key=key)
        return True
    return False


def send_payloads(ctx: IncidentContext, rows: list[dict], count: int) -> int:
    """Send ``count`` CSV payloads to the endpoint, cycling through ``rows``.

    Returns the number sent. No pacing — scenarios send short bursts.
    """
    if not ctx.runtime or not rows:
        return 0
    for i in range(count):
        row = rows[i % len(rows)]
        body = ",".join(str(row.get(f, "")) for f in FEATURE_ORDER)
        ctx.runtime.invoke_endpoint(
            EndpointName=ctx.endpoint_name, ContentType="text/csv", Body=body.encode("utf-8"),
        )
    return count
