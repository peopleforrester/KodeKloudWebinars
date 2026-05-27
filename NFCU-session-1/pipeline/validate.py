#!/usr/bin/env python3
# ABOUTME: Pre-deploy gate for the NFCU Session 1 pipeline; validates a model artifact
# ABOUTME: against schema, mutable-reference, and policy checks with distinct exit codes.
"""Validate a model artifact before it is allowed into a deployment.

Three independent checks run in order, each with its own exit code so a CI run's
failure cause is unambiguous:

    exit 2  Mutable artifact reference (checked first; short-circuits on rejection)
    exit 1  Schema check (signature.json structure)
    exit 3  Policy check (model card size, metadata completeness, min accuracy)
    exit 99 Internal error (any unhandled exception)
    exit 0  All checks passed

The artifact is a ``model-v*.tar.gz`` tarball. It may be referenced as a local
``file:///`` URI (offline) or an ``s3://`` URI (requires AWS credentials). The
artifact URI and model version may also be supplied via the ``ARTIFACT_URI`` and
``MODEL_VERSION`` environment variables for CI use.
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import os
import sys
import tarfile
import tempfile
from typing import Any
from urllib.parse import urlparse

import jsonschema

logging.basicConfig(level=logging.INFO, format="%(message)s")
LOG = logging.getLogger("validate")

# Exit codes (see module docstring).
EXIT_OK = 0
EXIT_SCHEMA = 1
EXIT_MUTABLE = 2
EXIT_POLICY = 3
EXIT_INTERNAL = 99

# Mutable identifiers that must never be used as an immutable model reference.
MUTABLE_REFERENCES = {"latest", "prod", "current", "stable", "main"}

MIN_MODEL_CARD_BYTES = 100
MIN_ACCURACY = 0.5
REQUIRED_METADATA_KEYS = ("training_run_id", "training_dataset", "evaluation")

# Expected structure of signature.json (the "documented schema").
SIGNATURE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["input", "output"],
    "properties": {
        "input": {
            "type": "object",
            "required": ["type", "properties", "required"],
            "properties": {
                "type": {"const": "object"},
                "properties": {"type": "object"},
                "required": {"type": "array"},
            },
        },
        "output": {
            "type": "object",
            "required": ["type", "properties"],
            "properties": {
                "type": {"const": "object"},
                "properties": {"type": "object"},
            },
        },
    },
}


class CheckFailure(Exception):
    """Raised when a validation check fails; carries the CI-visible exit code."""

    def __init__(self, exit_code: int, message: str) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.message = message


def read_artifact_members(artifact_uri: str) -> dict[str, bytes]:
    """Return the basename->bytes map of files inside the artifact tarball.

    Supports ``file:///`` (local) and ``s3://`` (downloaded via boto3) URIs.
    """
    parsed = urlparse(artifact_uri)
    if parsed.scheme == "file":
        local_path = parsed.path
        with open(local_path, "rb") as handle:
            raw = handle.read()
    elif parsed.scheme == "s3":
        import boto3  # imported lazily so offline file:// runs need no AWS deps

        with tempfile.NamedTemporaryFile() as tmp:
            boto3.client("s3").download_fileobj(parsed.netloc, parsed.path.lstrip("/"), tmp)
            tmp.seek(0)
            raw = tmp.read()
    else:
        raise CheckFailure(EXIT_INTERNAL, f"Unsupported artifact scheme: '{parsed.scheme}'")

    members: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:*") as tar:
        for member in tar.getmembers():
            if member.isfile():
                extracted = tar.extractfile(member)
                if extracted is not None:
                    members[os.path.basename(member.name)] = extracted.read()
    return members


def check_mutable_reference(model_version: str | None) -> None:
    """Reject mutable model references (exit 2). Runs first and short-circuits."""
    if model_version and model_version.strip().lower() in MUTABLE_REFERENCES:
        raise CheckFailure(
            EXIT_MUTABLE,
            f"VALIDATION FAILED: Mutable artifact reference — '{model_version}' "
            "is not allowed; use immutable semver",
        )


def check_schema(members: dict[str, bytes]) -> None:
    """Validate signature.json against the documented schema (exit 1)."""
    if "signature.json" not in members:
        raise CheckFailure(EXIT_SCHEMA, "VALIDATION FAILED: Schema check — signature.json missing from artifact")
    try:
        signature = json.loads(members["signature.json"])
    except json.JSONDecodeError as exc:
        raise CheckFailure(EXIT_SCHEMA, f"VALIDATION FAILED: Schema check — signature.json is not valid JSON: {exc}")
    try:
        jsonschema.validate(instance=signature, schema=SIGNATURE_SCHEMA)
    except jsonschema.ValidationError as exc:
        field = "/".join(str(p) for p in exc.absolute_path) or "(root)"
        raise CheckFailure(EXIT_SCHEMA, f"VALIDATION FAILED: Schema check — {field}: {exc.message}")


def check_policy(members: dict[str, bytes]) -> None:
    """Enforce model-card size, metadata completeness, min accuracy (exit 3)."""
    card = members.get("model_card.md", b"")
    if len(card) < MIN_MODEL_CARD_BYTES:
        raise CheckFailure(
            EXIT_POLICY,
            f"VALIDATION FAILED: Policy check — model_card.md is {len(card)} bytes; "
            f"minimum is {MIN_MODEL_CARD_BYTES}",
        )

    if "metadata.json" not in members:
        raise CheckFailure(EXIT_POLICY, "VALIDATION FAILED: Policy check — metadata.json missing from artifact")
    try:
        metadata = json.loads(members["metadata.json"])
    except json.JSONDecodeError as exc:
        raise CheckFailure(EXIT_POLICY, f"VALIDATION FAILED: Policy check — metadata.json is not valid JSON: {exc}")

    missing = [key for key in REQUIRED_METADATA_KEYS if key not in metadata]
    if missing:
        raise CheckFailure(
            EXIT_POLICY,
            f"VALIDATION FAILED: Policy check — metadata.json missing key(s): {', '.join(missing)}",
        )

    accuracy = metadata.get("evaluation", {}).get("accuracy")
    if not isinstance(accuracy, (int, float)):
        raise CheckFailure(EXIT_POLICY, "VALIDATION FAILED: Policy check — evaluation.accuracy is missing or non-numeric")
    if accuracy < MIN_ACCURACY:
        raise CheckFailure(
            EXIT_POLICY,
            f"VALIDATION FAILED: Policy check — evaluation.accuracy {accuracy} is below minimum {MIN_ACCURACY}",
        )


def run_validation(artifact_uri: str, model_version: str | None) -> None:
    """Run all checks in order. Raises CheckFailure on the first failure."""
    # Mutable-reference check runs first so a mutable version is rejected with
    # exit 2 before the artifact is even read (the deliberate Lab 1 failure path).
    check_mutable_reference(model_version)
    members = read_artifact_members(artifact_uri)
    check_schema(members)
    check_policy(members)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments, falling back to env vars for CI."""
    parser = argparse.ArgumentParser(description="Validate a model artifact before deploy.")
    parser.add_argument("--artifact", default=os.environ.get("ARTIFACT_URI"), help="file:// or s3:// artifact URI")
    parser.add_argument("--model-version", default=os.environ.get("MODEL_VERSION"), help="Model version reference")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns the appropriate exit code; never raises."""
    try:
        args = parse_args(argv)
        if not args.artifact:
            raise CheckFailure(EXIT_INTERNAL, "No artifact provided (use --artifact or ARTIFACT_URI)")
        run_validation(args.artifact, args.model_version)
    except CheckFailure as failure:
        LOG.error(failure.message)
        return failure.exit_code
    except Exception as exc:  # noqa: BLE001 - never let validation pass silently
        LOG.error("VALIDATION ERROR: Internal — %s: %s", type(exc).__name__, exc)
        return EXIT_INTERNAL
    LOG.info("VALIDATION PASSED: schema, reference, policy")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
