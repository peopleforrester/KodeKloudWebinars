// ABOUTME: k6 load test for the Lab 1 XGBoost InferenceService — drives concurrency-based
// ABOUTME: KServe autoscaling: ramp 1->100 VUs over 2m, hold 3m, ramp down 1m.
import http from 'k6/http';
import { check } from 'k6';
import { Counter, Trend } from 'k6/metrics';

// Cluster-specific, overridable via env:
//   BASE_URL   Kourier ingress (default kind: http://localhost:31080)
//   NAMESPACE  attendee namespace
//   DOMAIN     Knative domain (default example.com)
const BASE_URL = __ENV.BASE_URL || 'http://localhost:31080';
const NAMESPACE = __ENV.NAMESPACE || 'default';
const DOMAIN = __ENV.DOMAIN || 'example.com';
const SVC = 'adult-income-classifier';
const HOST = `${SVC}.${NAMESPACE}.${DOMAIN}`;
// Optional: header Knative/KServe can be configured to echo the serving revision in.
const REVISION_HEADER = __ENV.REVISION_HEADER || 'K-Revision';

const requestsPerRevision = new Counter('requests_per_revision');
const predictLatency = new Trend('predict_latency_ms', true);

export const options = {
  stages: [
    { duration: '2m', target: 100 }, // ramp up
    { duration: '3m', target: 100 }, // hold — KServe scales out on concurrency here
    { duration: '1m', target: 0 },   // ramp down — watch it scale back toward zero
  ],
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<2000'],
  },
};

const payload = JSON.stringify({
  instances: [[39, 7, 77516, 9, 13, 4, 1, 1, 4, 1, 2174, 0, 40, 39]],
});

export default function () {
  const res = http.post(`${BASE_URL}/v1/models/${SVC}:predict`, payload, {
    headers: { 'Content-Type': 'application/json', Host: HOST },
  });
  check(res, { 'status is 200': (r) => r.status === 200 });
  predictLatency.add(res.timings.duration);
  // Tag per revision when the cluster echoes it; otherwise read the authoritative
  // split from `kubectl get revisions` / Grafana (see tests/README.md).
  const revision = res.headers[REVISION_HEADER] || 'unknown';
  requestsPerRevision.add(1, { revision });
}
