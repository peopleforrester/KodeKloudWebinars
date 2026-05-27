# ABOUTME: Incident scenario 3 — isolated prediction drift (outputs inverted).
# ABOUTME: Swaps the endpoint to a session-3-owned inverted variant (OQ4 alt).
"""prediction_drift_isolated.

The model's *output* distribution flips while inputs look normal — the classic
signature of container/dependency corruption. Rare, and usually fixed by rollback
rather than by understanding the model.

OQ4 implementation note: the v2.1 doc's first choice is flipping an inference
container env var to invert outputs. That requires a hook in the Session 1/2
container that may not exist, and rebuilding that container would breach the
touch boundary into ``session-2/``. The in-scope alternative used here is a
**SageMaker endpoint-config swap** to a session-3-owned "inverted" variant
(``config['inverted_endpoint_config']``), reverted on cleanup. Both the inverted
and baseline endpoint configs are provided to the Lambda as configuration.

Routing (see runbook): DevOps first (rollback); escalate to the model owner only
if rollback does not restore correct behavior.
"""

from . import CLEANUP_AFTER_MINUTES, IncidentContext, clear_marker, write_marker

NAME = "prediction_drift_isolated"
EXPECTED_ALARM = "Drift-PSI"  # prediction-distribution drift (output side)


def trigger(ctx: IncidentContext) -> dict:
    inverted = ctx.config.get("inverted_endpoint_config")
    swapped = False
    if ctx.sagemaker and inverted:
        ctx.sagemaker.update_endpoint(
            EndpointName=ctx.endpoint_name, EndpointConfigName=inverted
        )
        swapped = True
    marker = write_marker(ctx, NAME, {"swapped_to": inverted})
    return {
        "scenario": NAME,
        "action": "trigger",
        "expected_alarm": ctx.alarm(EXPECTED_ALARM),
        "swapped_to_inverted_variant": swapped,
        "marker": marker,
    }


def cleanup(ctx: IncidentContext) -> dict:
    baseline = ctx.config.get("baseline_endpoint_config")
    reverted = False
    if ctx.sagemaker and baseline:
        ctx.sagemaker.update_endpoint(
            EndpointName=ctx.endpoint_name, EndpointConfigName=baseline
        )
        reverted = True
    cleared = clear_marker(ctx, NAME)
    return {"scenario": NAME, "action": "cleanup", "reverted_to_baseline": reverted,
            "cleared_marker": cleared}
