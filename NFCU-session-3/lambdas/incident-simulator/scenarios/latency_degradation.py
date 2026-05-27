# ABOUTME: Incident scenario 4 — latency degradation (~800ms in the inference path).
# ABOUTME: Swaps the endpoint to a session-3-owned slow variant; Latency-P95 fires.
"""latency_degradation.

Inference latency degrades by ~800ms while predictions stay correct — a pure
infrastructure incident. Implemented (in scope, no S1/2 container rebuild) by
swapping the endpoint to a session-3-owned "slow" variant that injects an 800ms
delay (``config['latency_endpoint_config']``), reverted on cleanup.

Routing (see runbook): DevOps almost always (capacity, noisy neighbors,
dependency latency).
"""

from . import CLEANUP_AFTER_MINUTES, IncidentContext, clear_marker, write_marker

NAME = "latency_degradation"
EXPECTED_ALARM = "Latency-P95"
INJECTED_LATENCY_MS = 800


def trigger(ctx: IncidentContext) -> dict:
    slow = ctx.config.get("latency_endpoint_config")
    swapped = False
    if ctx.sagemaker and slow:
        ctx.sagemaker.update_endpoint(
            EndpointName=ctx.endpoint_name, EndpointConfigName=slow
        )
        swapped = True
    marker = write_marker(ctx, NAME, {"injected_latency_ms": INJECTED_LATENCY_MS})
    return {
        "scenario": NAME,
        "action": "trigger",
        "expected_alarm": ctx.alarm(EXPECTED_ALARM),
        "injected_latency_ms": INJECTED_LATENCY_MS,
        "swapped_to_slow_variant": swapped,
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
