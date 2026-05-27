#!/usr/bin/env python
# ABOUTME: Trains the champion model (model-v1.0.0) on UCI Adult Census Income.
# ABOUTME: RandomForest(max_depth=6, n_estimators=100, random_state=42).
# SPDX-License-Identifier: Apache-2.0
"""Train the champion model, ``model-v1.0.0``."""

from __future__ import annotations

from _train import build_arg_parser, train_and_save
from sklearn.ensemble import RandomForestClassifier


def main() -> None:
    """Parse arguments and train/persist the champion model."""
    parser = build_arg_parser("Train the champion model (model-v1.0.0).", "model-v1.0.0.joblib")
    args = parser.parse_args()
    estimator = RandomForestClassifier(max_depth=6, n_estimators=100, random_state=42)
    train_and_save(
        version="model-v1.0.0",
        estimator=estimator,
        output=args.output,
        data_dir=args.data_dir,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
