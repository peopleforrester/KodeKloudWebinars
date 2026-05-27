# comparison Lambda

EventBridge-scheduled (every 5 minutes). Joins champion and challenger shadow
outputs by `request_id`, computes metrics, emits CloudWatch custom metrics, and
writes a comparison result with a promotion verdict.

## Environment

| Variable | Purpose |
|---|---|
| `SHADOW_LOG_BUCKET` | Source of shadow-log entries and challenger async outputs. |
| `COMPARISON_RESULTS_BUCKET` | Destination for `latest.json`, archives, watermark. |
| `PROMOTION_CRITERIA_PATH` | Path to the bundled `promotion-criteria.yaml`. |

## Metrics

CloudWatch namespace `Workshop/Session2`: `ShadowAgreementRate`,
`ShadowLatencyP95Delta`, `ShadowDisparateImpactRatio` (per protected group).

## Result file

`s3://$COMPARISON_RESULTS_BUCKET/latest.json` (and `archive/{ts}.json`) contains
`metrics`, `criteria_evaluated`, `promotion_check_status` (`ready`/`not_ready`),
`failure_reasons`, `evaluation_window_start`, `evaluation_window_end`.

Criteria evaluation lives in `criteria.py`, shared verbatim with the promotion
GitHub Actions workflow so the gate logic has a single source of truth.
