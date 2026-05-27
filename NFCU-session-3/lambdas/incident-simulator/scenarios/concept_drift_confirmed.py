# ABOUTME: Incident scenario 5 — concept drift confirmed via returning ground truth.
# ABOUTME: Pushes synthetic labels with a 20% accuracy drop (time-compressed, D6).
"""concept_drift_confirmed.

The relationship between features and the target has shifted: inputs look normal,
the model still returns 200s, but realized accuracy has fallen. This is confirmed
only when ground-truth labels return and disagree with predictions.

TIME-COMPRESSION NOTE (design decision D6): real concept drift in lending/fraud
manifests over **months** as ground truth slowly returns. This lab compresses it
into ~15 minutes by pushing a batch of synthetic ground-truth labels in which 20%
disagree with the model's predictions. Lab response timing is NOT generalizable to
real-world incident response — the matching runbook states this explicitly.

Routing (see runbook): page the model owner (retraining/recalibration decision).
"""

import json
import random

from . import CLEANUP_AFTER_MINUTES, IncidentContext, clear_marker, write_marker

NAME = "concept_drift_confirmed"
EXPECTED_ALARM = None  # surfaces via the NannyML estimate / EstimatedAUCDelta, not an alarm
EXPECTED_SIGNAL = "EstimatedAUCDelta"
ACCURACY_DROP = 0.20
GROUND_TRUTH_PREFIX = "ground-truth/"


def _synthetic_labels(n: int, accuracy_drop: float) -> list[dict]:
    """Generate (prediction, true_label) pairs where ``accuracy_drop`` disagree."""
    rng = random.Random(13)
    rows = []
    for _ in range(n):
        pred = rng.randint(0, 1)
        # With probability == accuracy_drop, the true label disagrees.
        true = (1 - pred) if rng.random() < accuracy_drop else pred
        rows.append({"y_pred": pred, "income": true})
    return rows


def trigger(ctx: IncidentContext) -> dict:
    n = int(ctx.config.get("label_count", 2000))
    labels = _synthetic_labels(n, ACCURACY_DROP)
    key = f"{GROUND_TRUTH_PREFIX}{ctx.attendee_id}/labels.jsonl"
    pushed = False
    if ctx.s3 and ctx.control_bucket:
        body = "\n".join(json.dumps(r) for r in labels).encode("utf-8")
        ctx.s3.put_object(Bucket=ctx.control_bucket, Key=key, Body=body)
        pushed = True
    marker = write_marker(ctx, NAME, {"labels_key": key, "accuracy_drop": ACCURACY_DROP})
    return {
        "scenario": NAME,
        "action": "trigger",
        "expected_alarm": None,
        "expected_signal": EXPECTED_SIGNAL,
        "accuracy_drop": ACCURACY_DROP,
        "labels_pushed": pushed,
        "marker": marker,
    }


def cleanup(ctx: IncidentContext) -> dict:
    key = f"{GROUND_TRUTH_PREFIX}{ctx.attendee_id}/labels.jsonl"
    removed = False
    if ctx.s3 and ctx.control_bucket:
        ctx.s3.delete_object(Bucket=ctx.control_bucket, Key=key)
        removed = True
    cleared = clear_marker(ctx, NAME)
    return {"scenario": NAME, "action": "cleanup", "labels_removed": removed,
            "cleared_marker": cleared}
