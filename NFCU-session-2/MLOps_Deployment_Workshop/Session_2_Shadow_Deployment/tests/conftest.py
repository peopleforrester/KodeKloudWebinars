# ABOUTME: Shared pytest fixtures and a loader for the hyphenated lambda handler dirs.
# ABOUTME: Provides moto AWS credentials, synthetic data, and the default criteria.
# SPDX-License-Identifier: Apache-2.0
"""Pytest fixtures for the Session 2 Lambda tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml

SESSION_DIR = Path(__file__).resolve().parent.parent
LAMBDAS = SESSION_DIR / "lambdas"
CRITERIA_FILE = SESSION_DIR / "config" / "promotion-criteria.yaml"


def _load_handler(lambda_name: str, module_name: str) -> ModuleType:
    """Load a handler module from a hyphenated lambda directory.

    Lambda dirs use hyphens and share the basename ``handler.py``, so they
    cannot be imported by package name. This loads each by file path under a
    unique module name and puts its directory on ``sys.path`` for sibling
    imports (e.g. ``criteria``).
    """
    lambda_dir = LAMBDAS / lambda_name
    if str(lambda_dir) not in sys.path:
        sys.path.insert(0, str(lambda_dir))
    spec = importlib.util.spec_from_file_location(module_name, lambda_dir / "handler.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set dummy AWS credentials so moto-backed boto3 clients construct."""
    for key in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.setenv(key, "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def shadow_mirror() -> ModuleType:
    """The shadow-mirror handler module."""
    return _load_handler("shadow-mirror", "shadow_mirror_handler")


@pytest.fixture
def comparison() -> ModuleType:
    """The comparison handler module."""
    return _load_handler("comparison", "comparison_handler")


@pytest.fixture
def traffic_generator() -> ModuleType:
    """The traffic-generator handler module."""
    return _load_handler("traffic-generator", "traffic_generator_handler")


@pytest.fixture
def promotion_criteria() -> dict[str, Any]:
    """The default promotion criteria, parsed from the shipped YAML."""
    return yaml.safe_load(CRITERIA_FILE.read_text())


@pytest.fixture
def sample_adult_rows() -> list[dict[str, Any]]:
    """A small synthetic batch of UCI-Adult-shaped feature rows."""
    return [
        {
            "age": 39,
            "workclass": "Private",
            "education": "Bachelors",
            "education-num": 13,
            "marital-status": "Never-married",
            "occupation": "Adm-clerical",
            "relationship": "Not-in-family",
            "race": "White",
            "sex": "Male",
            "capital-gain": 2174,
            "capital-loss": 0,
            "hours-per-week": 40,
            "native-country": "United-States",
            "fnlwgt": 77516,
        },
        {
            "age": 50,
            "workclass": "Self-emp",
            "education": "Masters",
            "education-num": 14,
            "marital-status": "Married",
            "occupation": "Exec-managerial",
            "relationship": "Husband",
            "race": "Black",
            "sex": "Female",
            "capital-gain": 0,
            "capital-loss": 0,
            "hours-per-week": 45,
            "native-country": "United-States",
            "fnlwgt": 83311,
        },
    ]
