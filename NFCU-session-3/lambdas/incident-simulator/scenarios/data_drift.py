# ABOUTME: Incident scenario 2 — data drift via the drift-simulator behavior.
# ABOUTME: Invokes the deployed drift-simulator inline (hours_per_week shift).
"""data_drift.

Reuses the drift-simulator behavior inline: invokes the deployed
``drift-simulator-{attendee_id}`` Lambda asynchronously so the same
``hours_per_week`` shift drives PSI past 0.25.

Routing (see runbook): page the model owner (recalibration/retraining is a model
decision); DevOps handles containment.
"""

from . import CLEANUP_AFTER_MINUTES, IncidentContext, clear_marker, write_marker

NAME = "data_drift"
EXPECTED_ALARM = "Drift-PSI"


def trigger(ctx: IncidentContext) -> dict:
    invoked = False
    if ctx.lambda_client:
        ctx.lambda_client.invoke(
            FunctionName=f"drift-simulator-{ctx.attendee_id}",
            InvocationType="Event",  # async; the simulator runs its own 5-min loop
            Payload=b"{}",
        )
        invoked = True
    marker = write_marker(ctx, NAME, {"invoked_drift_simulator": invoked})
    return {
        "scenario": NAME,
        "action": "trigger",
        "expected_alarm": ctx.alarm(EXPECTED_ALARM),
        "invoked_drift_simulator": invoked,
        "marker": marker,
    }


def cleanup(ctx: IncidentContext) -> dict:
    # The drift-simulator stops on its own after 5 min; nothing persistent.
    cleared = clear_marker(ctx, NAME)
    return {"scenario": NAME, "action": "cleanup", "cleared_marker": cleared}
