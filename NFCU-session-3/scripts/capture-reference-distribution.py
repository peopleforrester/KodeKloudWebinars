#!/usr/bin/env python3
# ABOUTME: Capture a per-feature reference distribution for drift detection.
# ABOUTME: Reads clean S1/2 prediction logs (S3) or the local UCI fixture -> reference.parquet.
"""Capture the reference distribution used by the drift-detector and the runners.

Run ONCE during lab build (per D7) against clean Session 1/2 traffic, not per
attendee and not at session time. The output ``reference.parquet`` holds a sample
of the eight lab input features and is uploaded to each attendee's
``workshop-lab-{attendee_id}-baseline`` bucket during provisioning.

Sources supported (auto-detected from ``--source``):
  * ``s3://bucket/prefix`` — newline-delimited JSON prediction logs, one record
    per line, each containing the eight feature keys.
  * ``*.jsonl`` / ``*.json`` — the same JSON-lines format, read locally.
  * any other path — CSV; the raw UCI ``adult.data``/``adult.test`` format
    (header-less, comma-space separated, trailing ``.`` on the label) is detected
    and parsed automatically.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("capture-reference")

# The eight lab input features. Canonical definition documented in
# shared/fixtures/uci-adult/README.md.
FEATURES: list[str] = [
    "age",
    "workclass",
    "education_num",
    "marital_status",
    "occupation",
    "race",
    "sex",
    "hours_per_week",
]
NUMERIC_FEATURES: set[str] = {"age", "education_num", "hours_per_week"}

# Raw UCI column order (15 fields including label).
UCI_COLUMNS: list[str] = [
    "age", "workclass", "fnlwgt", "education", "education_num",
    "marital_status", "occupation", "relationship", "race", "sex",
    "capital_gain", "capital_loss", "hours_per_week", "native_country", "income",
]
MISSING_TOKEN = "?"


def _read_s3_jsonl(source: str, region: str) -> pd.DataFrame:
    """Read newline-delimited JSON prediction logs from an S3 prefix.

    Args:
        source: An ``s3://bucket/prefix`` URI.
        region: AWS region for the S3 client.

    Returns:
        A DataFrame with one row per JSON record.

    Raises:
        ValueError: If no objects are found under the prefix.
    """
    import boto3  # imported lazily so local CSV runs need no AWS deps

    _, _, rest = source.partition("s3://")
    bucket, _, prefix = rest.partition("/")
    client = boto3.client("s3", region_name=region)
    paginator = client.get_paginator("list_objects_v2")

    keys: list[str] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        keys.extend(obj["Key"] for obj in page.get("Contents", []))
    if not keys:
        raise ValueError(f"No objects found under s3://{bucket}/{prefix}")

    logger.info("Reading %d prediction-log objects from s3://%s/%s", len(keys), bucket, prefix)
    records: list[dict] = []
    for i, key in enumerate(keys, start=1):
        body = client.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
        for line in body.splitlines():
            line = line.strip()
            if line:
                records.append(json.loads(line))
        if i % 50 == 0 or i == len(keys):
            logger.info("  ... %d/%d objects (%d records)", i, len(keys), len(records))
    return pd.DataFrame.from_records(records)


def _read_local_jsonl(path: Path) -> pd.DataFrame:
    """Read newline-delimited JSON records from a local file."""
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return pd.DataFrame.from_records(records)


def _read_uci_csv(path: Path) -> pd.DataFrame:
    """Read the raw UCI Adult CSV format, cleaning UCI-specific quirks."""
    df = pd.read_csv(
        path,
        header=None,
        names=UCI_COLUMNS,
        skipinitialspace=True,
        comment="|",            # drops the "|1x3 Cross validator" line
        na_values=[MISSING_TOKEN],
    )
    # The test split appends a trailing "." to the income label; harmless here
    # because income is not one of the eight features, but normalise anyway.
    if "income" in df.columns:
        df["income"] = df["income"].astype(str).str.rstrip(".").str.strip()
    return df


def load_source(source: str, region: str) -> pd.DataFrame:
    """Load raw records from any supported source into a DataFrame."""
    if source.startswith("s3://"):
        return _read_s3_jsonl(source, region)
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Source not found: {source}")
    if path.suffix in {".jsonl", ".json"}:
        return _read_local_jsonl(path)
    return _read_uci_csv(path)


def build_reference(df: pd.DataFrame, min_rows: int) -> pd.DataFrame:
    """Select the eight features, clean them, and validate row count.

    Args:
        df: Raw source records.
        min_rows: Minimum acceptable row count after cleaning.

    Returns:
        A DataFrame with exactly the eight feature columns.

    Raises:
        ValueError: If a feature is missing or too few clean rows remain.
    """
    missing = [f for f in FEATURES if f not in df.columns]
    if missing:
        raise ValueError(f"Source is missing required feature columns: {missing}")

    ref = df[FEATURES].copy()
    for col in NUMERIC_FEATURES:
        ref[col] = pd.to_numeric(ref[col], errors="coerce")
    before = len(ref)
    ref = ref.dropna()
    logger.info("Dropped %d rows with missing values (%d -> %d)", before - len(ref), before, len(ref))

    if len(ref) < min_rows:
        raise ValueError(
            f"Only {len(ref)} clean rows available; need at least {min_rows}. "
            "Refusing to write an under-sized reference (no silent fallback)."
        )
    return ref.reset_index(drop=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default=str(Path(__file__).resolve().parent.parent / "shared/fixtures/uci-adult/adult.test"),
        help="s3://bucket/prefix, a .jsonl file, or a UCI CSV (default: bundled fixture)",
    )
    parser.add_argument("--output", default="reference.parquet", help="Output parquet path")
    parser.add_argument("--min-rows", type=int, default=1000, help="Minimum clean rows required")
    parser.add_argument("--region", default="us-east-1", help="AWS region for S3 sources")
    args = parser.parse_args(argv)

    logger.info("Loading source: %s", args.source)
    df = load_source(args.source, args.region)
    logger.info("Loaded %d raw records", len(df))

    ref = build_reference(df, args.min_rows)
    ref.to_parquet(args.output, index=False)
    logger.info(
        "Wrote %s: %d rows x %d features %s",
        args.output, len(ref), len(ref.columns), list(ref.columns),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
