# ABOUTME: Tests for the drift-simulator Lambda: drift transform + traffic volume.
# ABOUTME: Verifies only hours_per_week is shifted and the request count is correct.
import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sim(import_lambda):
    return import_lambda("drift-simulator", "handler")


def _sample_df(n: int = 500) -> pd.DataFrame:
    rng = np.random.default_rng(5)
    return pd.DataFrame({
        "age": rng.integers(18, 80, n),
        "workclass": rng.choice(["Private", "Gov"], n),
        "education_num": rng.integers(1, 16, n),
        "marital_status": rng.choice(["Married", "Single"], n),
        "occupation": rng.choice(["Tech", "Sales"], n),
        "race": rng.choice(["A", "B"], n),
        "sex": rng.choice(["Male", "Female"], n),
        "hours_per_week": rng.integers(20, 60, n).astype(float),
    })


def test_apply_drift_only_shifts_hours_per_week(sim):
    df = _sample_df()
    drifted = sim.apply_drift(df, seed=1)
    # Every non-target column is untouched.
    for col in df.columns:
        if col != "hours_per_week":
            pd.testing.assert_series_equal(df[col], drifted[col])
    # hours_per_week moved up (mean +15) and is clipped to [0, 100].
    assert drifted["hours_per_week"].mean() > df["hours_per_week"].mean() + 8
    assert drifted["hours_per_week"].between(0, 100).all()


def test_send_traffic_sends_expected_count(sim):
    rows = _sample_df(100).to_dict(orient="records")
    sent = []
    count = sim.send_traffic(
        invoke=lambda body: sent.append(body),
        rows=rows,
        rate_per_s=10,
        duration_s=300,
        sleep=lambda _s: None,  # collapse pacing for the test
    )
    assert count == 3000
    assert len(sent) == 3000


def test_handler_sends_3000_drifted_only(sim, monkeypatch):
    source = _sample_df(200)
    captured = []

    monkeypatch.setattr(sim, "_load_samples", lambda *a, **k: source)
    monkeypatch.setattr(sim, "_make_invoker", lambda *a, **k: (lambda body: captured.append(body)))
    monkeypatch.setattr(sim.time, "sleep", lambda _s: None)
    monkeypatch.setenv("ATTENDEE_ID", "lab-007")
    monkeypatch.setenv("ENDPOINT_NAME", "workshop-lab-007-production")

    result = sim.handler({}, None)

    assert result["drifted_feature"] == "hours_per_week"
    assert abs(result["requests_sent"] - 3000) <= 50
    assert len(captured) == result["requests_sent"]

    # Reconstruct hours_per_week from the CSV payloads; it should be shifted up
    # relative to the source sample (drift), while staying within [0, 100].
    sent_hours = [float(body.split(",")[sim.FEATURE_ORDER.index("hours_per_week")]) for body in captured]
    assert max(sent_hours) <= 100
    assert np.mean(sent_hours) > source["hours_per_week"].mean()
