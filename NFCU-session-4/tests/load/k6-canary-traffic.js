// ABOUTME: k6 steady traffic for the Lab 4 canary — 5 RPS for 5 minutes, enough to observe
// ABOUTME: the ~10% split without triggering autoscaling beyond minReplicas.
import http from 'k6/http';
import { check } from 'k6';
import { Counter } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:31080';
const NAMESPACE = __ENV.NAMESPACE || 'default';
const DOMAIN = __ENV.DOMAIN || 'example.com';
const SVC = 'adult-income-classifier';
const HOST = `${SVC}.${NAMESPACE}.${DOMAIN}`;
const REVISION_HEADER = __ENV.REVISION_HEADER || 'K-Revision';

// Per-revision tally. With ~10% canary you expect ~8-12% on the new revision.
const requestsPerRevision = new Counter('requests_per_revision');

export const options = {
  scenarios: {
    steady: {
      executor: 'constant-arrival-rate',
      rate: 5, // 5 requests/second
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 10,
      maxVUs: 20,
    },
  },
  thresholds: { http_req_failed: ['rate<0.02'] },
};

const payload = JSON.stringify({
  instances: [[39, 7, 77516, 9, 13, 4, 1, 1, 4, 1, 2174, 0, 40, 39]],
});

export default function () {
  const res = http.post(`${BASE_URL}/v1/models/${SVC}:predict`, payload, {
    headers: { 'Content-Type': 'application/json', Host: HOST },
  });
  check(res, { 'status is 200': (r) => r.status === 200 });
  // The split is authoritatively read from `kubectl get revisions` / Grafana. If your
  // cluster echoes the serving revision in a response header, this also tags it here.
  const revision = res.headers[REVISION_HEADER] || 'unknown';
  requestsPerRevision.add(1, { revision });
}
