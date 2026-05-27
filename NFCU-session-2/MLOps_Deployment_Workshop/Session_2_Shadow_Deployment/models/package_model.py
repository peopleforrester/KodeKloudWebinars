#!/usr/bin/env python
# ABOUTME: Packages a joblib pipeline + inference.py into a SageMaker model tar.gz.
# ABOUTME: Produces model.joblib at the root and code/inference.py for the container.
# SPDX-License-Identifier: Apache-2.0
"""Package a trained joblib model into the SageMaker ``model.tar.gz`` layout.

Layout produced::

    model.tar.gz
    ├── model.joblib
    └── code/
        └── inference.py
"""

from __future__ import annotations

import argparse
import tarfile
from pathlib import Path


def package(input_path: Path, output_path: Path, inference_path: Path) -> Path:
    """Bundle the model and inference script into a gzip tarball.

    Args:
        input_path: Path to the trained ``.joblib`` pipeline.
        output_path: Destination ``.tar.gz`` path.
        inference_path: Path to the ``inference.py`` entry point to bundle.

    Returns:
        The output path.

    Raises:
        FileNotFoundError: If the model or inference script is missing.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Model artifact not found: {input_path}")
    if not inference_path.exists():
        raise FileNotFoundError(f"Inference script not found: {inference_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output_path, "w:gz") as tar:
        tar.add(input_path, arcname="model.joblib")
        tar.add(inference_path, arcname="code/inference.py")
    print(f"Packaged {input_path.name} -> {output_path}")
    return output_path


def main() -> None:
    """Parse arguments and package the model."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Trained .joblib model.")
    parser.add_argument("--output", type=Path, required=True, help="Destination .tar.gz.")
    parser.add_argument(
        "--inference",
        type=Path,
        default=Path(__file__).resolve().parent / "inference.py",
        help="Inference entry point to bundle (default: models/inference.py).",
    )
    args = parser.parse_args()
    package(args.input, args.output, args.inference)


if __name__ == "__main__":
    main()
