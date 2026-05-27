// ABOUTME: k6 load test for the Lab 3 TinyLlama endpoint — a gentle 1->10 VU ramp that
// ABOUTME: stays within containerConcurrency(5) x maxReplicas(3)=15 so 5xx stays under 1%.
import http from 'k6/http';
import { check } from 'k6';
import { Trend, Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:31080';
const NAMESPACE = __ENV.NAMESPACE || 'default';
const DOMAIN = __ENV.DOMAIN || 'example.com';
const SVC = 'tinyllama-completion';
const HOST = `${SVC}.${NAMESPACE}.${DOMAIN}`;

const genLatency = new Trend('generation_latency_ms', true);
const errorRate = new Rate('llm_errors');

export const options = {
  stages: [
    { duration: '1m', target: 10 }, // gentle ramp — LLM inference is heavy on CPU
    { duration: '3m', target: 10 }, // steady state
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    // Spec: error rate under 1% during steady state.
    llm_errors: ['rate<0.01'],
  },
};

const payload = JSON.stringify({
  prompt: 'The future of cloud-native ML is',
  max_tokens: 50,
});

export default function () {
  const res = http.post(`${BASE_URL}/v1/models/${SVC}:predict`, payload, {
    headers: { 'Content-Type': 'application/json', Host: HOST },
    timeout: '60s', // CPU generation can be slow; do not count slow-but-ok as an error
  });
  const ok = check(res, {
    'status is 200': (r) => r.status === 200,
    'has completion': (r) => {
      try {
        return (r.json('completion') || '').length > 0;
      } catch (e) {
        return false;
      }
    },
  });
  errorRate.add(!ok);
  genLatency.add(res.timings.duration);
}
