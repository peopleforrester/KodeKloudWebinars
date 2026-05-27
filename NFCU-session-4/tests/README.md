# Tests

Smoke tests and k6 load scripts, one per lab traffic pattern. Smoke runs first (fast fail);
load scripts drive the scaling and canary behavior the labs teach.

## Smoke (run before any load test)

```bash
bash smoke/curl-tests.sh    # one prediction to each endpoint; non-zero exit names the failure
```

`curl-tests.sh` sends `smoke/sample-payload-xgboost.json` to the XGBoost service and
`smoke/sample-payload-llm.json` to TinyLlama. Each must return 200 within 5 seconds.

## Load (k6)

| Script | Lab | Traffic pattern |
|---|---|---|
| `load/k6-xgboost-kserve.js` | 2 | 1→100 VUs over 2m, hold 3m, ramp down 1m — drives KServe concurrency scaling |
| `load/k6-xgboost-hpa.js` | 2 | Same ramp against the HPA baseline (for comparison) |
| `load/k6-tinyllama.js` | 3 | Gentle 1→10 VUs (stays under `containerConcurrency 5 × maxReplicas 3`) |
| `load/k6-canary-traffic.js` | 4 | Steady 5 RPS for 5m — observe the canary split without extra autoscaling |

```bash
# Point k6 at your ingress. Local kind default is http://localhost:31080.
BASE_URL=http://localhost:31080 NAMESPACE=default k6 run load/k6-xgboost-kserve.js

# Compare KServe vs HPA scaling side by side:
NAMESPACE=default bash load/compare-scaling.sh
```

### Environment variables

| Var | Default | Meaning |
|---|---|---|
| `BASE_URL` | `http://localhost:31080` | Kourier ingress URL |
| `NAMESPACE` | `default` | Attendee namespace |
| `DOMAIN` | `example.com` | Knative domain (sets the `Host` header) |
| `REVISION_HEADER` | `K-Revision` | Response header to tag per-revision counts, if your cluster echoes it |

## Observing scale and the canary split

k6 reports throughput, latency, and error rate. Two things k6 cannot see directly:

- **Pod count over time** — `compare-scaling.sh` samples it with `kubectl` during the run
  and prints time-to-scale-up, peak, and time-to-scale-down. Or watch live:
  `kubectl get pods -n <ns> -w`.
- **Per-revision traffic split (canary)** — the authoritative source is Knative:
  `kubectl get revisions -n <ns>` and the Knative/KServe Grafana dashboards. The k6 scripts
  also tag a `requests_per_revision` counter from the `K-Revision` response header *if* your
  cluster is configured to echo it; otherwise that counter reads `unknown` and you rely on
  the Knative metrics. With a 10% canary, expect 8–12% on the new revision.

## Note

k6 is not bundled with this repo (install from <https://k6.io>). The scripts are authored and
reviewed but are executed against a live cluster, not in repo CI.
