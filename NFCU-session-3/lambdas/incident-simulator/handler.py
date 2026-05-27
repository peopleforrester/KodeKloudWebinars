# ABOUTME: incident-simulator Lambda — round-robin scenario assignment + dispatch.
# ABOUTME: Assigns one of five scenarios by attendee index and triggers/cleans up.
"""incident-simulator.

The lab platform passes a 0-indexed ``attendee_index``; the handler assigns one of
five scenarios in **round-robin** order (design decision D4) so a 30-person cohort
gets ~6 of each — random assignment would skew the Slide 18 debrief.

Event fields:
* ``attendee_id`` (or env ``ATTENDEE_ID``) — sandbox id.
* ``attendee_index`` (or env ``ATTENDEE_INDEX``) — 0-indexed cohort position.
* ``action`` — ``"trigger"`` (default) or ``"cleanup"``.
* ``scenario`` — optional 1–5 override (otherwise round-robin).
"""

import os

import boto3

from scenarios import (
    IncidentContext,
    concept_drift_confirmed,
    data_drift,
    feature_pipeline_broken,
    latency_degradation,
    prediction_drift_isolated,
)

# Scenario numbers are stable (1–5) so the round-robin and the debrief line up.
SCENARIOS = {
    1: feature_pipeline_broken,
    2: data_drift,
    3: prediction_drift_isolated,
    4: latency_degradation,
    5: concept_drift_confirmed,
}
NUM_SCENARIOS = len(SCENARIOS)


def assign_scenario(attendee_index: int) -> int:
    """Round-robin: 0-indexed attendee -> scenario number in [1, 5]."""
    return (attendee_index % NUM_SCENARIOS) + 1


def _build_context(attendee_id: str) -> IncidentContext:
    region = os.environ.get("AWS_REGION", "us-east-1")
    return IncidentContext(
        attendee_id=attendee_id,
        endpoint_name=os.environ.get("ENDPOINT_NAME", f"workshop-lab-{attendee_id}-production"),
        region=region,
        control_bucket=os.environ.get("DRIFT_REPORTS_BUCKET", f"workshop-lab-{attendee_id}-drift-reports"),
        sagemaker=boto3.client("sagemaker", region_name=region),
        runtime=boto3.client("sagemaker-runtime", region_name=region),
        s3=boto3.client("s3", region_name=region),
        lambda_client=boto3.client("lambda", region_name=region),
        config={
            "baseline_endpoint_config": os.environ.get("BASELINE_ENDPOINT_CONFIG", ""),
            "inverted_endpoint_config": os.environ.get("INVERTED_ENDPOINT_CONFIG", ""),
            "latency_endpoint_config": os.environ.get("LATENCY_ENDPOINT_CONFIG", ""),
        },
    )


def handler(event, context):
    """Entry point. Triggers (or cleans up) the assigned scenario."""
    event = event or {}
    attendee_id = event.get("attendee_id") or os.environ["ATTENDEE_ID"]
    attendee_index = int(event.get("attendee_index", os.environ.get("ATTENDEE_INDEX", "0")))
    action = event.get("action", "trigger")

    scenario_n = int(event["scenario"]) if event.get("scenario") else assign_scenario(attendee_index)
    if scenario_n not in SCENARIOS:
        raise ValueError(f"scenario must be in 1..{NUM_SCENARIOS}, got {scenario_n}")
    module = SCENARIOS[scenario_n]

    ctx = _build_context(attendee_id)
    result = module.cleanup(ctx) if action == "cleanup" else module.trigger(ctx)
    result.update({
        "scenario_number": scenario_n,
        "attendee_id": attendee_id,
        "attendee_index": attendee_index,
        "cleanup_after_minutes": module.CLEANUP_AFTER_MINUTES,
    })
    return result
