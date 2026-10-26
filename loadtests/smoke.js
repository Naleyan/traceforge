import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export const options = {
  vus: 5,
  duration: '30s',
  summaryTrendStats: ['avg', 'min', 'med', 'p(95)', 'p(99)', 'max'],
};

export default function () {
  const payload = JSON.stringify({ product_id: 'p1', quantity: 1 });
  const params = { headers: { 'Content-Type': 'application/json' } };

  const res = http.post(`${BASE_URL}/orders`, payload, params);

  check(res, {
    'status is 201': (r) => r.status === 201,
    'order is paid': (r) => r.json('status') === 'paid',
  });

  sleep(1);
}