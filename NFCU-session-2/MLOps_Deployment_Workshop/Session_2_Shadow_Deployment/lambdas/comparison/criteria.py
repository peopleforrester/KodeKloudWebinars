# ABOUTME: Pure promotion-criteria evaluator shared by the comparison Lambda,
# ABOUTME: the promote workflow (CLI), and the unit tests — one source of truth.
# SPDX-License-Identifier: Apache-2.0
"""Evaluate shadow-comparison metrics against the promotion criteria.

This module is intentionally dependency-light (stdlib + PyYAML) so it can run
inside the comparison Lambda, be invoked by the promotion GitHub Actions
workflow, and be unit-tested directly. It performs no I/O except in the CLI
entry point.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, TypedDict

import yaml

READY = "ready"
NOT_READY = "not_ready"


class CriterionResult(TypedDict):
    """One evaluated criterion."""

    passed: bool
    actual: Any
    required: Any


class EvaluationResult(TypedDict):
    """Outcome of evaluating all promotion criteria."""

    promotion_check_status: str
    criteria_evaluated: dict[str, CriterionResult]
    failure_reasons: list[str]


def evaluate_criteria(metrics: dict[str, Any], criteria: dict[str, Any]) -> EvaluationResult:
    """Evaluate ``metrics`` against the ``promotion_criteria`` thresholds.

    Args:
        metrics: Computed shadow metrics (see the comparison Lambda for shape).
        criteria: Parsed ``promotion-criteria.yaml`` (top-level mapping).

    Returns:
        An :class:`EvaluationResult` with overall status, per-criterion detail,
        and human-readable failure reasons (empty when ready).
    """
    pc = criteria["promotion_criteria"]
    evaluated: dict[str, CriterionResult] = {}
    failures: list[str] = []

    def record(name: str, passed: bool, actual: Any, required: Any, reason: str) -> None:
        evaluated[name] = {"passed": passed, "actual": actual, "required": required}
        if not passed:
            failures.append(reason)

    # Observation volume -----------------------------------------------------
    n_obs = int(metrics.get("n_observations", 0))
    min_obs = int(pc["minimum_observations"])
    record(
        "minimum_observations",
        n_obs >= min_obs,
        n_obs,
        min_obs,
        f"{n_obs} observations, minimum {min_obs} required",
    )

    per_group = metrics.get("observations_per_protected_group", {})
    min_group = min(per_group.values()) if per_group else 0
    min_group_required = int(pc["minimum_observations_per_protected_group"])
    record(
        "minimum_observations_per_protected_group",
        min_group >= min_group_required,
        min_group,
        min_group_required,
        f"smallest protected group has {min_group} observations, "
        f"minimum {min_group_required} required",
    )

    # Agreement rate ---------------------------------------------------------
    agreement = float(metrics.get("agreement_rate", 0.0))
    ag_min = float(pc["agreement_rate"]["minimum"])
    ag_max = float(pc["agreement_rate"]["maximum"])
    record(
        "agreement_rate_minimum",
        agreement >= ag_min,
        agreement,
        ag_min,
        f"agreement_rate {agreement} below minimum {ag_min}",
    )
    record(
        "agreement_rate_maximum",
        agreement <= ag_max,
        agreement,
        ag_max,
        f"agreement_rate {agreement} exceeds maximum {ag_max} "
        "(challenger may not be meaningfully different from champion)",
    )

    # Latency ----------------------------------------------------------------
    challenger_p95 = float(metrics.get("latency_p95_challenger_ms", 0.0))
    challenger_max = float(pc["latency_p95_ms"]["challenger_max"])
    record(
        "latency_p95_challenger_max",
        challenger_p95 <= challenger_max,
        challenger_p95,
        challenger_max,
        f"challenger p95 latency {challenger_p95}ms exceeds max {challenger_max}ms",
    )
    delta_pct = float(metrics.get("latency_p95_delta_pct", 0.0))
    delta_max = float(pc["latency_p95_ms"]["delta_vs_champion_max_pct"])
    record(
        "latency_p95_delta_vs_champion",
        delta_pct <= delta_max,
        delta_pct,
        delta_max,
        f"challenger p95 latency is {delta_pct}% slower than champion, max allowed {delta_max}%",
    )

    # Disparate impact -------------------------------------------------------
    di = metrics.get("disparate_impact", {})
    min_ratio_challenger = float(di.get("min_ratio_challenger", 0.0))
    max_ratio_per_group = float(pc["disparate_impact"]["max_ratio_per_group"])
    record(
        "disparate_impact_min_ratio",
        min_ratio_challenger >= max_ratio_per_group,
        min_ratio_challenger,
        max_ratio_per_group,
        f"challenger smallest protected-group ratio {min_ratio_challenger} "
        f"below required {max_ratio_per_group}",
    )
    if pc["disparate_impact"].get("must_not_be_worse_than_champion", False):
        min_ratio_champion = float(di.get("min_ratio_champion", 0.0))
        record(
            "disparate_impact_not_worse_than_champion",
            min_ratio_challenger >= min_ratio_champion,
            min_ratio_challenger,
            min_ratio_champion,
            f"challenger disparate-impact ratio {min_ratio_challenger} is worse "
            f"than champion {min_ratio_champion}",
        )

    status = READY if not failures else NOT_READY
    return {
        "promotion_check_status": status,
        "criteria_evaluated": evaluated,
        "failure_reasons": failures,
    }


def _main(argv: list[str] | None = None) -> int:
    """CLI used by the promotion workflow: evaluate a result file in place.

    Reads the comparison metrics JSON and the criteria YAML, prints the verdict
    as JSON, and exits non-zero when the challenger is not ready.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", required=True, help="Path to a comparison result JSON.")
    parser.add_argument("--criteria", required=True, help="Path to promotion-criteria.yaml.")
    args = parser.parse_args(argv)

    with open(args.metrics) as fh:
        result = json.load(fh)
    metrics = result.get("metrics", result)
    with open(args.criteria) as fh:
        criteria = yaml.safe_load(fh)

    verdict = evaluate_criteria(metrics, criteria)
    json.dump(verdict, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if verdict["promotion_check_status"] == READY else 1


if __name__ == "__main__":
    raise SystemExit(_main())
