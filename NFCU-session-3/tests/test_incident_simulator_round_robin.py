# ABOUTME: Tests for incident-simulator round-robin assignment + scenario dispatch.
# ABOUTME: Confirms even distribution across 30 attendees and the scenario interface.
from collections import Counter

import pytest


@pytest.fixture
def sim(import_lambda):
    return import_lambda("incident-simulator", "handler")


def test_round_robin_even_across_30(sim):
    counts = Counter(sim.assign_scenario(i) for i in range(30))
    # Exactly six of each of the five scenarios — no skew (design decision D4).
    assert counts == {1: 6, 2: 6, 3: 6, 4: 6, 5: 6}


def test_assign_scenario_range(sim):
    assert {sim.assign_scenario(i) for i in range(100)} == {1, 2, 3, 4, 5}


def test_every_scenario_has_the_interface(sim):
    for number, module in sim.SCENARIOS.items():
        assert isinstance(module.NAME, str)
        assert hasattr(module, "EXPECTED_ALARM")
        assert module.CLEANUP_AFTER_MINUTES == 15
        assert callable(module.trigger)
        assert callable(module.cleanup)


class _StubRuntime:
    def __init__(self):
        self.calls = 0

    def invoke_endpoint(self, **kwargs):
        self.calls += 1
        return {"Body": b""}


class _StubS3:
    def __init__(self):
        self.puts = {}
        self.deletes = []

    def put_object(self, Bucket, Key, Body, **kwargs):
        self.puts[(Bucket, Key)] = Body

    def delete_object(self, Bucket, Key, **kwargs):
        self.deletes.append((Bucket, Key))


class _StubSageMaker:
    def __init__(self):
        self.updates = []

    def update_endpoint(self, EndpointName, EndpointConfigName):
        self.updates.append((EndpointName, EndpointConfigName))


def _stub_ctx(sim):
    return sim.IncidentContext(
        attendee_id="lab-007",
        endpoint_name="workshop-lab-007-production",
        control_bucket="workshop-lab-007-drift-reports",
        runtime=_StubRuntime(),
        s3=_StubS3(),
        sagemaker=_StubSageMaker(),
        config={"baseline_endpoint_config": "cfg-base",
                "inverted_endpoint_config": "cfg-inverted",
                "latency_endpoint_config": "cfg-slow"},
    )


def test_handler_triggers_feature_pipeline_scenario(sim, monkeypatch):
    ctx = _stub_ctx(sim)
    monkeypatch.setattr(sim, "_build_context", lambda attendee_id: ctx)

    result = sim.handler({"attendee_id": "lab-007", "scenario": 1}, None)

    assert result["scenario_number"] == 1
    assert result["scenario"] == "feature_pipeline_broken"
    assert result["cleanup_after_minutes"] == 15
    assert result["requests_sent"] == 600
    assert result["expected_alarm"] == "Drift-PSI-lab-007"
    # Burst actually went to the endpoint and a control marker was written.
    assert ctx.runtime.calls == 600
    assert ("workshop-lab-007-drift-reports", "incident-control/feature_pipeline_broken.json") in ctx.s3.puts


def test_handler_index_4_assigns_concept_drift_and_cleans_up(sim, monkeypatch):
    ctx = _stub_ctx(sim)
    monkeypatch.setattr(sim, "_build_context", lambda attendee_id: ctx)

    # attendee_index 4 -> scenario 5 (concept_drift_confirmed).
    triggered = sim.handler({"attendee_id": "lab-007", "attendee_index": 4}, None)
    assert triggered["scenario_number"] == 5
    assert triggered["scenario"] == "concept_drift_confirmed"
    assert triggered["accuracy_drop"] == 0.20
    assert triggered["labels_pushed"] is True

    cleaned = sim.handler({"attendee_id": "lab-007", "attendee_index": 4, "action": "cleanup"}, None)
    assert cleaned["labels_removed"] is True
    assert cleaned["cleared_marker"] is True


def test_handler_prediction_drift_swaps_and_reverts_variant(sim, monkeypatch):
    ctx = _stub_ctx(sim)
    monkeypatch.setattr(sim, "_build_context", lambda attendee_id: ctx)

    sim.handler({"attendee_id": "lab-007", "scenario": 3}, None)
    sim.handler({"attendee_id": "lab-007", "scenario": 3, "action": "cleanup"}, None)
    # Swapped to inverted on trigger, back to baseline on cleanup.
    assert ctx.sagemaker.updates == [
        ("workshop-lab-007-production", "cfg-inverted"),
        ("workshop-lab-007-production", "cfg-base"),
    ]
