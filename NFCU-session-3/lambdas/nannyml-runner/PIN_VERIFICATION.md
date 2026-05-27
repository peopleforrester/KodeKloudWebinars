# NannyML Pin Verification

**Pinned range (build-time):** `nannyml>=0.12,<0.14` — lock to an exact version
once re-verified.
**API style:** `nml.CBPE(y_pred_proba=, y_pred=, y_true=, metrics=['roc_auc'],
chunk_size=, problem_type='classification_binary')`; `.fit(reference_df)`;
`.estimate(analysis_df)`; results read via
`results.filter(period='analysis').to_df()` (estimated value under the
`roc_auc` / `value` column).

## Re-verification window (design decision D1 / task 5.1)

Re-verify on PyPI **no earlier than June 9, 2026**.

- Lock the exact latest-stable version.
- **Confirm the `CBPE` constructor signature still matches `handler.py`**
  (`y_pred_proba`, `y_pred`, `y_true`, `problem_type`, `metrics`). NannyML has
  changed argument names across minor versions; this is the highest-risk item.
- Confirm `results.filter(period='analysis').to_df()` still exposes the `roc_auc`
  value column (the handler's `_mean_estimated_auc` reader handles both MultiIndex
  and flat column layouts defensively).

## Verification log

| Date | Checked by | Latest on PyPI | Decision | Notes |
|------|-----------|----------------|----------|-------|
| 2026-05-27 | build | _not checked — before window_ | **hold range** | CBPE API surface verified against the NannyML stable docs (binary standard-metric estimation tutorial). Exact PyPI version re-check is date-gated to ≥ June 9. |
| _≥ June 9_ | _pending_ | _pending_ | _pending_ | Required before session day; lock exact version. |

## API source of truth

NannyML stable docs — "Estimating Standard Performance Metrics for Binary
Classification" (CBPE) tutorial.
