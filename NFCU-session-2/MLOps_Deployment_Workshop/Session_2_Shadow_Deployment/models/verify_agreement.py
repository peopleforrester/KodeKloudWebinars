#!/usr/bin/env python
# ABOUTME: Lab-engineer helper: reports champion/challenger agreement on the test split.
# ABOUTME: Must land 90-94%; writes the disagreement-region row IDs for the traffic generator.
# SPDX-License-Identifier: Apache-2.0
"""Verify the engineered agreement rate between champion and challenger.

Loads ``model-v1.0.0.joblib`` and ``model-v1.0.1.joblib``, scores the UCI Adult
test split, and reports the fraction of rows where both models predict the same
label. The lab targets a 90-94% agreement rate. The indices of the disagreeing
rows are written out so the traffic generator can bias samples toward that
region.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
from _dataset import default_data_dir, load_adult

TARGET_MIN = 0.90
TARGET_MAX = 0.94


def _parse_s3_uri(uri: str) -> tuple[str, str]:
    """Split an ``s3://bucket/key`` URI into ``(bucket, key)``."""
    without_scheme = uri.removeprefix("s3://")
    bucket, _, key = without_scheme.partition("/")
    return bucket, key


def main() -> int:
    """Compute the agreement rate and persist the disagreement region.

    Returns:
        Process exit code: 0 if the agreement rate is within the 90-94% target
        band, 1 otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    models_dir = Path(__file__).resolve().parent
    parser.add_argument("--champion", type=Path, default=models_dir / "model-v1.0.0.joblib")
    parser.add_argument("--challenger", type=Path, default=models_dir / "model-v1.0.1.joblib")
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument(
        "--out",
        type=Path,
        default=default_data_dir() / "disagreement_region.json",
        help="Local path for the disagreement-region row IDs.",
    )
    parser.add_argument(
        "--s3-uri",
        type=str,
        default=None,
        help="Optional s3://bucket/key to upload the disagreement region to.",
    )
    args = parser.parse_args()

    for path in (args.champion, args.challenger):
        if not path.exists():
            print(
                f"ERROR: missing model {path}. Run train_champion.py and "
                "train_challenger.py first.",
                file=sys.stderr,
            )
            return 1

    champion = joblib.load(args.champion)
    challenger = joblib.load(args.challenger)

    _, _, x_test, _ = load_adult(args.data_dir or default_data_dir())
    champion_pred = champion.predict(x_test)
    challenger_pred = challenger.predict(x_test)

    matches = champion_pred == challenger_pred
    agreement = float(matches.mean())
    disagreement_indices = [int(i) for i in range(len(matches)) if not matches[i]]

    print(f"Observations:        {len(matches):,}")
    print(f"Agreements:          {int(matches.sum()):,}")
    print(f"Disagreements:       {len(disagreement_indices):,}")
    print(f"Agreement rate:      {agreement:.4f}")
    print(f"Target band:         {TARGET_MIN:.2f}-{TARGET_MAX:.2f}")

    payload = {
        "agreement_rate": agreement,
        "n_observations": int(len(matches)),
        "disagreement_row_indices": disagreement_indices,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2))
    print(f"Wrote disagreement region -> {args.out}")

    if args.s3_uri:
        import boto3

        bucket, key = _parse_s3_uri(args.s3_uri)
        boto3.client("s3").put_object(
            Bucket=bucket, Key=key, Body=json.dumps(payload).encode("utf-8")
        )
        print(f"Uploaded disagreement region -> {args.s3_uri}")

    if not TARGET_MIN <= agreement <= TARGET_MAX:
        print(
            f"FAIL: agreement {agreement:.4f} is outside the "
            f"{TARGET_MIN:.2f}-{TARGET_MAX:.2f} target band.",
            file=sys.stderr,
        )
        return 1
    print("PASS: agreement rate within target band.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
