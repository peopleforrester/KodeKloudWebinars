# shadow-mirror Lambda

API Gateway-fronted fan-out. Invokes the **champion** endpoint synchronously and
returns only its response to the caller; mirrors the request to the
**challenger** endpoint asynchronously so challenger latency or failure can never
affect the caller ("zero member impact").

## Environment

| Variable | Purpose |
|---|---|
| `CHAMPION_ENDPOINT_ARN` | Champion endpoint name or ARN (sync invoke). |
| `CHALLENGER_ENDPOINT_ARN` | Challenger endpoint name or ARN (async invoke). |
| `SHADOW_LOG_BUCKET` | Bucket for async inputs and shadow-log entries. |

The promotion workflow performs the traffic flip by swapping the two
`*_ENDPOINT_ARN` variables.

## Output

- Caller response: `{"prediction", "endpoint_source": "champion", "request_id"}`.
- Shadow log: `s3://$SHADOW_LOG_BUCKET/raw/year=YYYY/month=MM/day=DD/{request_id}.json`
  with timestamp, request_id, input payload, champion response, and the
  challenger async output URI.
