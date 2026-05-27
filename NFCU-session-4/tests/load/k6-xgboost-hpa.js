// ABOUTME: k6 load test for the Lab 2 HPA baseline Deployment — the SAME ramp as the
// ABOUTME: KServe test, so the CPU-HPA scaling lag is directly comparable.
import http from 'k6/http';
import { check } from 'k6';
import { Trend } from 'k6/metrics';

// The HPA baseline is a plain Service (ClusterIP). Point BASE_URL at it via port-forward
// or a NodePort, e.g.:  kubectl -n <ns> port-forward svc/xgboost-hpa-baseline 8081:80
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8081';
const SVC = 'adult-income';            // --model_name passed to xgbserver in the Deployment
const predictLatency = new Trend('predict_latency_ms', true);

export const options = {
  // Identical to k6-xgboost-kserve.js so the two runs are apples-to-apples.
  stages: [
    { duration: '2m', target: 100 },
    { duration: '3m', target: 100 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.10'], // the baseline is expected to struggle — looser bound
  },
};

const payload = JSON.stringify({
  instances: [[39, 7, 77516, 9, 13, 4, 1, 1, 4, 1, 2174, 0, 40, 39]],
});

export default function () {
  const res = http.post(`${BASE_URL}/v1/models/${SVC}:predict`, payload, {
    headers: { 'Content-Type': 'application/json' },
  });
  check(res, { 'status is 200': (r) => r.status === 200 });
  predictLatency.add(res.timings.duration);
}
