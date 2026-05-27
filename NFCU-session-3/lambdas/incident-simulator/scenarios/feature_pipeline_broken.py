# ABOUTME: Incident scenario 1 — upstream feature pipeline emits NULL workclass.
# ABOUTME: Sends null-workclass payloads for ~5 min; workclass PSI spikes.
"""feature_pipeline_broken.

Simulates a broken upstream feature pipeline that drops the ``workclass`` field
(emits NULL). The model keeps returning 200s, but the workclass distribution
collapses to empty — caught by per-feature PSI, not by infrastructure metrics.

Routing (see runbook): usually DevOps (data infra); page the model owner only if
the root cause is a schema change requiring retraining.
"""

import random

from . import (
    CLEANUP_AFTER_MINUTES,
    IncidentContext,
    clear_marker,
    send_payloads,
    write_marker,
)

NAME = "feature_pipeline_broken"
EXPECTED_ALARM = "Drift-PSI"  # workclass distribution collapses to NULL
BURST = 600  # payloads (~5 min of degraded traffic at lab rates)


def _null_workclass_rows(n: int = 200) -> list[dict]:
    rng = random.Random(7)
    rows = []
    for _ in range(n):
        rows.append({
            "age": rng.randint(18, 80),
            "workclass": "",  # NULL — the broken field
            "education_num": rng.randint(1, 16),
            "marital_status": rng.choice(["Married", "Single"]),
            "occupation": rng.choice(["Tech", "Sales", "Admin"]),
            "race": rng.choice(["A", "B", "C"]),
            "sex": rng.choice(["Male", "Female"]),
            "hours_per_week": rng.randint(20, 60),
        })
    return rows


def trigger(ctx: IncidentContext) -> dict:
    sent = send_payloads(ctx, _null_workclass_rows(), BURST)
    marker = write_marker(ctx, NAME, {"requests_sent": sent})
    return {
        "scenario": NAME,
        "action": "trigger",
        "expected_alarm": ctx.alarm(EXPECTED_ALARM),
        "requests_sent": sent,
        "marker": marker,
    }


def cleanup(ctx: IncidentContext) -> dict:
    # Traffic-driven incident: stopping the null-workclass burst is the
    # remediation. There is no persistent infrastructure to revert.
    cleared = clear_marker(ctx, NAME)
    return {"scenario": NAME, "action": "cleanup", "cleared_marker": cleared}
