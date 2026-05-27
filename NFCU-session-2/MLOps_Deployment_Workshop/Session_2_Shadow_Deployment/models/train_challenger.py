#!/usr/bin/env python
# ABOUTME: Trains the challenger model (model-v1.0.1) on UCI Adult Census Income.
# ABOUTME: RandomForest(max_depth=16, n_estimators=80, max_features=0.3, random_state=42).
# SPDX-License-Identifier: Apache-2.0
"""Train the challenger model, ``model-v1.0.1``.

The hyperparameters are chosen to produce ~92% prediction agreement with the
champion on the UCI Adult test split — meaningful enough to teach a comparison
without requiring a multi-week shadow run.

Dry-run record: the proposal's illustrative ``max_depth=8, n_estimators=150``
empirically produced ~97.5% agreement (too similar to the champion to teach a
useful comparison). Per the design's validation requirement ("if it doesn't
land in 90-94%, retrain model-v1.0.1 with adjusted hyperparameters"), the
challenger was retuned to the values below, which yield ~0.928 agreement and
~0.861 accuracy. See models/README.md for the full dry-run table.
"""

from __future__ import annotations

from _train import build_arg_parser, train_and_save
from sklearn.ensemble import RandomForestClassifier


def main() -> None:
    """Parse arguments and train/persist the challenger model."""
    parser = build_arg_parser("Train the challenger model (model-v1.0.1).", "model-v1.0.1.joblib")
    args = parser.parse_args()
    estimator = RandomForestClassifier(
        max_depth=16, n_estimators=80, max_features=0.3, random_state=42
    )
    train_and_save(
        version="model-v1.0.1",
        estimator=estimator,
        output=args.output,
        data_dir=args.data_dir,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
