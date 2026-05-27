# ABOUTME: Tests for per-feature PSI computation (Population Stability Index).
# ABOUTME: Covers identical, heavily-shifted, zero-count-bin, and categorical cases.
import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def psi(import_lambda):
    return import_lambda("drift-detector", "psi")


def test_identical_distributions_psi_near_zero(psi):
    rng = np.random.default_rng(42)
    data = pd.Series(rng.normal(40, 12, size=5000))
    value = psi.compute_psi(data, data.copy())
    assert value == pytest.approx(0.0, abs=1e-9)


def test_mild_sampling_noise_stays_below_threshold(psi):
    rng = np.random.default_rng(0)
    reference = pd.Series(rng.normal(40, 12, size=10000))
    current = pd.Series(rng.normal(40, 12, size=10000))
    # Same distribution, different draws -> PSI well under the 0.25 alarm line.
    assert psi.compute_psi(reference, current) < 0.1


def test_heavily_shifted_distribution_exceeds_threshold(psi):
    rng = np.random.default_rng(1)
    reference = pd.Series(rng.normal(40, 12, size=10000))
    # hours_per_week-style shift: +25 mean is far beyond the 0.25 alarm line.
    current = pd.Series(rng.normal(65, 12, size=10000))
    assert psi.compute_psi(reference, current) > 0.25


def test_zero_count_bin_is_finite(psi):
    # Current data collapses into a narrow range, leaving several
    # reference-defined bins with zero current observations.
    rng = np.random.default_rng(7)
    reference = pd.Series(rng.uniform(0, 100, size=5000))
    current = pd.Series(rng.uniform(40, 45, size=5000))
    value = psi.compute_psi(reference, current)
    assert np.isfinite(value)  # epsilon prevents division-by-zero / log(0)
    assert value > 0.25        # and it still registers as significant drift


def test_categorical_psi(psi):
    reference = pd.Series(["Private"] * 700 + ["Self-emp"] * 200 + ["Gov"] * 100)
    # Shift the mix heavily toward Gov.
    current = pd.Series(["Private"] * 300 + ["Self-emp"] * 200 + ["Gov"] * 500)
    value = psi.compute_psi(reference, current)
    assert np.isfinite(value)
    assert value > 0.25


def test_categorical_identical_near_zero(psi):
    reference = pd.Series(["Private"] * 700 + ["Self-emp"] * 200 + ["Gov"] * 100)
    value = psi.compute_psi(reference, reference.copy())
    assert value == pytest.approx(0.0, abs=1e-9)


def test_unseen_category_in_current_is_finite(psi):
    reference = pd.Series(["Private"] * 800 + ["Gov"] * 200)
    current = pd.Series(["Private"] * 500 + ["Gov"] * 200 + ["Never-worked"] * 300)
    value = psi.compute_psi(reference, current)
    assert np.isfinite(value)
    assert value > 0.0
