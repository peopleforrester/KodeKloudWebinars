# Evidently Pin Verification

**Pinned version:** `evidently==0.7.21`
**API style:** 0.7.x — `from evidently import Dataset, DataDefinition, Report`;
`from evidently.presets import DataDriftPreset, DataQualityPreset`;
`Dataset.from_pandas(df, data_definition=DataDefinition(...))`;
`report.run(current, reference)`; `my_eval.save_html(path)`. The legacy
`column_mapping` argument is **not** used.

## Re-verification window (design decision D1)

The pin **MUST** be re-verified on PyPI **no earlier than June 9, 2026** and **no
later than June 11**.

- If a stable **0.7.22+** is available → bump the pin and re-test against the
  fixture data (the API is stable within 0.7.x).
- If a **0.8.x** is available → **do NOT auto-bump.** Halt and escalate to Michael;
  the API may have changed and Task 4.1 needs review.

## Verification log

| Date | Checked by | Latest on PyPI | Decision | Notes |
|------|-----------|----------------|----------|-------|
| 2026-05-27 | build | _not checked — before window_ | **hold at 0.7.21** | API surface verified against the official 0.7.x README quickstart (imports, `report.run`, `save_html`). PyPI version re-check is date-gated to ≥ June 9; not performed. |
| _≥ June 9_ | _pending_ | _pending_ | _pending_ | Required before session day. |

## API source of truth

0.7.x API confirmed against the Evidently README quickstart (evidentlyai/evidently,
`main`): `from evidently import Report`, `from evidently.presets import
DataDriftPreset`, `report.run(current, reference)`, and `my_eval.save_html("file.html")`.
The older `from evidently.report import Report` path (0.4.x) is **not** used.
