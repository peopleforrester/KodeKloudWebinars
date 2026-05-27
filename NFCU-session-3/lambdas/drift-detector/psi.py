# ABOUTME: Population Stability Index (PSI) computed per feature, numeric or categorical.
# ABOUTME: Used by the drift-detector Lambda to quantify per-feature distribution shift.
"""Per-feature PSI.

PSI measures how much a single feature's distribution has shifted between a
reference window and a current window. Working thresholds (model-risk convention):

* ``< 0.10`` — stable
* ``0.10 – 0.25`` — moderate shift, investigate
* ``> 0.25`` — significant shift, alarm

PSI is intentionally computed **per feature** (never as a single aggregate), so
the drifting feature is identifiable.
"""

import numpy as np
import pandas as pd

# Replaces zero proportions so the log and ratio stay finite when a bin or
# category has no observations in one of the windows.
_EPSILON = 1e-6


def _psi_from_proportions(ref_pct: np.ndarray, cur_pct: np.ndarray) -> float:
    """PSI from two aligned proportion vectors.

    Args:
        ref_pct: Reference-window proportions (sum ~ 1).
        cur_pct: Current-window proportions (sum ~ 1), aligned to ``ref_pct``.

    Returns:
        The PSI value as a float.
    """
    ref_pct = np.clip(ref_pct, _EPSILON, None)
    cur_pct = np.clip(cur_pct, _EPSILON, None)
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def _numeric_psi(reference: pd.Series, current: pd.Series, bins: int) -> float:
    """PSI for a numeric feature using reference-quantile bin edges."""
    ref = reference.dropna().to_numpy(dtype=float)
    cur = current.dropna().to_numpy(dtype=float)
    if ref.size == 0 or cur.size == 0:
        return 0.0

    # Bin edges from reference quantiles (equal-frequency reference bins).
    quantiles = np.linspace(0.0, 1.0, bins + 1)
    edges = np.unique(np.quantile(ref, quantiles))
    if edges.size < 2:
        # Degenerate reference (constant feature) — no measurable shift basis.
        return 0.0
    # Make outer edges inclusive of any out-of-range current values.
    edges[0], edges[-1] = -np.inf, np.inf

    ref_counts, _ = np.histogram(ref, bins=edges)
    cur_counts, _ = np.histogram(cur, bins=edges)
    ref_pct = ref_counts / ref_counts.sum()
    cur_pct = cur_counts / cur_counts.sum()
    return _psi_from_proportions(ref_pct, cur_pct)


def _categorical_psi(reference: pd.Series, current: pd.Series) -> float:
    """PSI for a categorical feature over the union of observed categories."""
    ref_counts = reference.dropna().astype(str).value_counts()
    cur_counts = current.dropna().astype(str).value_counts()
    categories = ref_counts.index.union(cur_counts.index)
    if len(categories) == 0:
        return 0.0
    ref_pct = (ref_counts.reindex(categories, fill_value=0).to_numpy(dtype=float)
               / ref_counts.sum())
    cur_pct = (cur_counts.reindex(categories, fill_value=0).to_numpy(dtype=float)
               / cur_counts.sum())
    return _psi_from_proportions(ref_pct, cur_pct)


def compute_psi(reference: pd.Series, current: pd.Series, bins: int = 10) -> float:
    """Compute the Population Stability Index for one feature.

    Numeric features are binned by reference quantiles; categorical features are
    compared over the union of observed categories. A small epsilon keeps the
    result finite when a bin or category is empty in one window.

    Args:
        reference: The reference-window values for a single feature.
        current: The current-window values for the same feature.
        bins: Number of bins for numeric features (ignored for categorical).

    Returns:
        The PSI value as a non-negative float.
    """
    if pd.api.types.is_numeric_dtype(reference):
        return _numeric_psi(reference, current, bins)
    return _categorical_psi(reference, current)
