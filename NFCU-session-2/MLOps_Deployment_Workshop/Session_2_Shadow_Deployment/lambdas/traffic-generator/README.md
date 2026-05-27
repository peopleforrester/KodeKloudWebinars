# traffic-generator Lambda

Manually invoked to drive synthetic load against the shadow-mirror endpoint
during the lab. Reads the UCI Adult test split and the disagreement-region row
IDs from S3 and biases ~15% of samples toward that region so the comparison
shows a meaningful number of disagreements.

## Invocation

```json
{"duration_minutes": 5, "rate": 10, "seed": 42}
```

## Environment

| Variable | Purpose |
|---|---|
| `SHADOW_MIRROR_URL` | Shadow-mirror API Gateway URL (POST target). |
| `TEST_DATA_URI` | `s3://...` JSON array of UCI Adult test rows. |
| `DISAGREEMENT_REGION_URI` | `s3://...` JSON from `verify_agreement.py` with `disagreement_row_indices`. |

## Output

`{"requests_sent", "failures", "average_latency_ms"}`. Non-2xx responses are
counted as failures and do not abort the run.
