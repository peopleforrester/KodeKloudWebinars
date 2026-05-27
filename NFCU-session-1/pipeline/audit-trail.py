#!/usr/bin/env python3
# ABOUTME: Final production-deploy step; writes an immutable audit record to S3 so any
# ABOUTME: prediction can be traced back to its training run (the five-minute trace test).
"""Write the production-deploy audit record to S3.

Runs as the last step of the production deploy workflow. Assembles a single JSON
object with all fields required to trace a deployed endpoint back to its training
run, then writes it to:

    s3://<AUDIT_BUCKET>/audit/{YYYY-MM-DD}/{git_commit_sha}.json

Every field must be non-null; a missing input fails the step (the deploy is not
considered successful without a complete audit event). Transient S3 5xx errors are
retried with exponential backoff (5 attempts, ~30s total); if all attempts fail,
the step fails.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(message)s")
LOG = logging.getLogger("audit-trail")

SCHEMA_VERSION = 1
EVENT = "production_deploy_completed"
MAX_ATTEMPTS = 5
# Backoff between attempts: 2, 4, 8, 16 seconds (~30s total across 4 retries).
BACKOFF_BASE_SECONDS = 2


class AuditError(Exception):
    """Raised when the audit record cannot be assembled or written."""


def _required(name: str) -> str:
    """Return a required environment variable or raise if it is missing/empty."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise AuditError(f"Required input '{name}' is missing or empty")
    return value


def build_record() -> dict[str, object]:
    """Assemble the ordered audit record from environment variables.

    ``schema_version`` is first; key insertion order is preserved on serialization.
    """
    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = _required("GITHUB_REPOSITORY")
    run_id = _required("GITHUB_RUN_ID")
    model_version = _required("MODEL_VERSION")

    record: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "event": EVENT,
        "endpoint_arn": _required("ENDPOINT_ARN"),
        "endpoint_version": model_version,
        "container_digest": _required("CONTAINER_DIGEST"),
        "artifact_version": model_version,
        "artifact_s3_uri": _required("ARTIFACT_S3_URI"),
        "training_run_id": _required("TRAINING_RUN_ID"),
        "training_dataset": _required("TRAINING_DATASET"),
        "git_commit_sha": _required("GITHUB_SHA"),
        "git_repo": repo,
        "approver_identity": _required("APPROVER_IDENTITY"),
        "change_ticket_reference": _required("CHANGE_TICKET_REFERENCE"),
        "deployment_workflow_run_url": f"{server_url}/{repo}/actions/runs/{run_id}",
    }

    null_fields = [key for key, value in record.items() if value is None or value == ""]
    if null_fields:
        raise AuditError(f"Audit record has null field(s): {', '.join(null_fields)}")
    return record


def _is_transient(error: Exception) -> bool:
    """Return True for retryable S3 errors (5xx or connection failures)."""
    from botocore.exceptions import ClientError, ConnectionError as BotoConnectionError, EndpointConnectionError

    if isinstance(error, (BotoConnectionError, EndpointConnectionError)):
        return True
    if isinstance(error, ClientError):
        status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)
        return status >= 500
    return False


def put_record(bucket: str, key: str, body: bytes) -> None:
    """Write the record to S3, retrying transient 5xx errors with backoff."""
    import boto3

    client = boto3.client("s3")
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            client.put_object(Bucket=bucket, Key=key, Body=body, ContentType="application/json")
            LOG.info("Audit record written to s3://%s/%s", bucket, key)
            return
        except Exception as error:  # noqa: BLE001 - classify then re-raise non-transient
            if not _is_transient(error) or attempt == MAX_ATTEMPTS:
                raise
            sleep_for = BACKOFF_BASE_SECONDS ** attempt
            LOG.warning("S3 write attempt %d/%d failed (transient): %s; retrying in %ds",
                        attempt, MAX_ATTEMPTS, error, sleep_for)
            time.sleep(sleep_for)


def main() -> int:
    """Entry point. Returns 0 on success, non-zero on failure."""
    try:
        bucket = _required("AUDIT_BUCKET")
        record = build_record()
        date = record["timestamp"][:10]  # YYYY-MM-DD from the ISO timestamp
        key = f"audit/{date}/{record['git_commit_sha']}.json"
        body = (json.dumps(record, indent=2) + "\n").encode("utf-8")
        put_record(bucket, key, body)
    except AuditError as error:
        LOG.error("AUDIT FAILED: %s", error)
        return 1
    except Exception as error:  # noqa: BLE001 - deploy is not successful without the audit event
        LOG.error("AUDIT FAILED: S3 write error — %s: %s", type(error).__name__, error)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
