# ABOUTME: Shared training routine for the champion and challenger trainers.
# ABOUTME: Trains the shared pipeline on UCI Adult and persists a joblib artifact.
# SPDX-License-Identifier: Apache-2.0
"""Common training entry point shared by the champion and challenger scripts."""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
from _dataset import build_pipeline, default_data_dir, load_adult
from sklearn.ensemble import RandomForestClassifier


def build_arg_parser(description: str, default_output: str) -> argparse.ArgumentParser:
    """Build the shared CLI parser for a trainer.

    Args:
        description: Help text for the trainer.
        default_output: Default joblib output filename.

    Returns:
        A configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / default_output,
        help="Path to write the trained joblib model.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Dataset cache directory (defaults to models/data/).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and exit without downloading or training.",
    )
    return parser


def train_and_save(
    *,
    version: str,
    estimator: RandomForestClassifier,
    output: Path,
    data_dir: Path | None,
    dry_run: bool,
) -> Path | None:
    """Train ``estimator`` on UCI Adult and persist the fitted pipeline.

    Args:
        version: Human-readable model version (e.g. ``model-v1.0.0``).
        estimator: The classifier to train.
        output: Destination joblib path.
        data_dir: Dataset cache directory, or ``None`` for the default.
        dry_run: If true, print the planned configuration and return ``None``.

    Returns:
        The output path on a real run, or ``None`` for a dry run.
    """
    params = estimator.get_params()
    print(
        f"{version}: RandomForestClassifier("
        f"max_depth={params['max_depth']}, "
        f"n_estimators={params['n_estimators']}, "
        f"random_state={params['random_state']})"
    )
    if dry_run:
        print(f"{version}: dry run — configuration valid, no training performed.")
        return None

    x_train, y_train, _, _ = load_adult(data_dir or default_data_dir())
    pipeline = build_pipeline(estimator)
    pipeline.fit(x_train, y_train)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, output)
    print(f"{version}: trained on {len(x_train):,} rows -> {output}")
    return output
