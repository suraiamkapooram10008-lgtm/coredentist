/**
 * CoreDent API Load Test
 * Uses k6 for performance testing of critical endpoints
 * 
 * Run: k6 run load_test.js
 * 
 * Scenarios:
 *   - Auth: Login and token refresh
 *   - Patients: CRUD operations
 *   - Appointments: Scheduling
 *   - Billing: Invoice creation
 *   - Search: Patient search
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const authDuration = new Trend('auth_duration');
const patientDuration = new Trend('patient_duration');
const appointmentDuration = new Trend('appointment_duration');
const billingDuration = new Trend('billing_duration');
const searchDuration = new Trend('search_duration');
const errorRate = new Rate('error_rate');

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000';
const VUS = parseInt(__ENV.VUS) || 10;
const DURATION = __ENV.DURATION || '30s';

export const options = {
  scenarios: {
    // Steady load: sustained traffic simulation
    steady_load: {
      executor: 'constant-vus',
      vus: VUS,
      duration: DURATION,
      exec: 'steadyLoad',
    },
    // Spike test: sudden traffic surge
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 50 },
        { duration: '10s', target: 50 },
        { duration: '10s', target: 0 },
      ],
      exec: 'spikeLoad',
      startTime: '30s',
    },
    // Stress test: increasing load
    stress: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '20s', target: 20 },
        { duration: '20s', target: 40 },
        { duration: '20s', target: 60 },
        { duration: '20s', target: 80 },
        { duration: '10s', target: 0 },
      ],
      exec: 'stressLoad',
      startTime: '60s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests under 500ms
    http_req_failed: ['rate<0.05'],     // <5% failure rate
    auth_duration: ['p(95)<1000'],
    patient_duration: ['p(95)<300'],
    appointment_duration: ['p(95)<300'],
    billing_duration: ['p(95)<500'],
    search_duration: ['p(95)<200'],
  },
};

// Test user credentials (use test environment)
const TEST_USER = {
  email: 'loadtest@coredent.com',
  password: 'TestPassword123!',
};

// Shared state across VUs
let authToken = '';
let practiceId = '';
let patientIds = [];
let appointmentIds = [];

export function setup() {
  // Create test user and practice
  const createResp = http.post(`${BASE_URL}/api/v1/auth/register`, JSON.stringify({
    email: TEST_USER.email,
    password: TEST_USER.password,
    first_name: 'Load',
    last_name: 'Test',
  }), { headers: { 'Content-Type': 'application/json' } });
  
  // Login to get token
  const loginResp = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify(TEST_USER), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  if (loginResp.status === 200) {
    const body = JSON.parse(loginResp.body);
    authToken = body.access_token;
    practiceId = body.practice_id;
  }
  
  return { authToken, practiceId };
}

// ====================== Steady Load Scenario ======================
export function steadyLoad() {
  group('Authentication', () => {
    const start = Date.now();
    const resp = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify(TEST_USER), {
      headers: { 'Content-Type': 'application/json' },
    });
    authDuration.add(Date.now() - start);
    check(resp, { 'login status 200': (r) => r.status === 200 });
    errorRate.add(resp.status !== 200);
    sleep(1);
  });

  group('Patient Search', () => {
    const start = Date.now();
    const resp = http.get(`${BASE_URL}/api/v1/patients?limit=10`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
    });
    searchDuration.add(Date.now() - start);
    check(resp, { 'search status 200': (r) => r.status === 200 });
    errorRate.add(resp.status !== 200);
  });

  group('Create Patient', () => {
    const start = Date.now();
    const patient = {
      first_name: `Load`,
      last_name: `Patient_${__VU}`,
      email: `load_${__VU}_${Date.now()}@test.com`,
      phone: `+1555${String(__VU).padStart(7, '0')}`,
      date_of_birth: '1990-01-01',
      gender: 'male',
    };
    const resp = http.post(`${BASE_URL}/api/v1/patients`, JSON.stringify(patient), {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`,
      },
    });
    patientDuration.add(Date.now() - start);
    if (resp.status === 201) {
      patientIds.push(JSON.parse(resp.body).id);
    }
    check(resp, { 'create patient 201': (r) => r.status === 201 });
    errorRate.add(resp.status !== 201);
    sleep(0.5);
  });

  group('Create Appointment', () => {
    if (patientIds.length > 0) {
      const start = Date.now();
      const appt = {
        patient_id: patientIds[patientIds.length - 1],
        appointment_type: 'cleaning',
        start_time: new Date(Date.now() + 86400000).toISOString(),
        duration: 60,
        notes: 'Load test appointment',
      };
      const resp = http.post(`${BASE_URL}/api/v1/appointments`, JSON.stringify(appt), {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
      });
      appointmentDuration.add(Date.now() - start);
      check(resp, { 'create appointment 201': (r) => r.status === 201 });
      errorRate.add(resp.status !== 201);
    }
  });

  group('Health Check', () => {
    const resp = http.get(`${BASE_URL}/api/v1/health`);
    check(resp, { 'health status 200': (r) => r.status === 200 });
  });
}

// ====================== Spike Load Scenario ======================
export function spikeLoad() {
  const endpoints = [
    `${BASE_URL}/api/v1/health`,
    `${BASE_URL}/api/v1/patients?limit=5`,
    `${BASE_URL}/api/v1/appointments?limit=5`,
    `${BASE_URL}/api/v1/billing/invoices?limit=5`,
  ];
  
  // Rapid-fire requests without waiting
  for (const url of endpoints) {
    const resp = http.get(url, {
      headers: { 'Authorization': `Bearer ${authToken}` },
    });
    check(resp, { 'spike endpoint ok': (r) => r.status < 500 });
  }
}

// ====================== Stress Load Scenario ======================
export function stressLoad() {
  group('Billing Operations', () => {
    const start = Date.now();
    const invoice = {
      patient_id: patientIds.length > 0 ? patientIds[0] : null,
      items: [
        { description: 'Cleaning', quantity: 1, unit_price: 100 },
        { description: 'X-Ray', quantity: 2, unit_price: 50 },
      ],
      due_date: new Date(Date.now() + 30 * 86400000).toISOString().split('T')[0],
    };
    const resp = http.post(`${BASE_URL}/api/v1/billing/invoices`, JSON.stringify(invoice), {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`,
      },
    });
    billingDuration.add(Date.now() - start);
    check(resp, { 'create invoice ok': (r) => r.status < 500 });
    errorRate.add(resp.status >= 400);
  });

  // Rate limiter test: hit login rapidly
  group('Rate Limit Test', () => {
    for (let i = 0; i < 10; i++) {
      const resp = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
        email: `bad_${i}@test.com`,
        password: 'wrong',
      }), { headers: { 'Content-Type': 'application/json' } });
      // Rate limited requests are expected (429)
      if (resp.status === 429) {
        // Rate limiting is working correctly
        check(resp, { 'rate limited correctly': (r) => r.status === 429 });
        break;
      }
    }
  });
}

export function teardown() {
  // Cleanup: delete created patients
  for (const pid of patientIds) {
    http.del(`${BASE_URL}/api/v1/patients/${pid}`, null, {
      headers: { 'Authorization': `Bearer ${authToken}` },
    });
  }
}