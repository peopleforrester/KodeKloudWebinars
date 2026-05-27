# ABOUTME: Tests the criteria.py CLI used by the promote workflow to gate promotion.
# ABOUTME: Verifies exit codes and verdict JSON for ready and not-ready results.
# SPDX-License-Identifier: Apache-2.0
"""Tests for the shared promotion-criteria CLI (`criteria.py`)."""

from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType

import pytest

CRITERIA_YAML = Path(__file__).resolve().parents[2] / "config" / "promotion-criteria.yaml"


@pytest.fixture
def criteria_module(comparison: ModuleType) -> ModuleType:
    """Import criteria.py (the comparison fixture puts its dir on sys.path)."""
    import criteria

    return criteria


def _write_result(path: Path, *, agreement: float) -> None:
    result = {
        "metrics": {
            "agreement_rate": agreement,
            "n_observations": 1500,
            "latency_p95_challenger_ms": 150.0,
            "latency_p95_delta_pct": 8.0,
            "observations_per_protected_group": {"Male|White": 800, "Female|Black": 700},
            "disparate_impact": {"min_ratio_challenger": 0.86, "min_ratio_champion": 0.82},
        }
    }
    path.write_text(json.dumps(result))


def test_cli_ready_exits_zero(
    criteria_module: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result_file = tmp_path / "latest.json"
    _write_result(result_file, agreement=0.92)
    code = criteria_module._main(["--metrics", str(result_file), "--criteria", str(CRITERIA_YAML)])
    assert code == 0
    assert json.loads(capsys.readouterr().out)["promotion_check_status"] == "ready"


def test_cli_not_ready_exits_one(
    criteria_module: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result_file = tmp_path / "latest.json"
    _write_result(result_file, agreement=0.995)
    code = criteria_module._main(["--metrics", str(result_file), "--criteria", str(CRITERIA_YAML)])
    assert code == 1
    verdict = json.loads(capsys.readouterr().out)
    assert verdict["promotion_check_status"] == "not_ready"
    assert any("exceeds maximum" in r for r in verdict["failure_reasons"])
