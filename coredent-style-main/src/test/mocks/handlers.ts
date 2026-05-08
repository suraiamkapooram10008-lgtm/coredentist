// Mock API handlers for testing
import { http, HttpResponse } from 'msw';
import type { Patient, Appointment } from '@/types/api';

const API_BASE_URL = '/api/v1';

export const handlers = [
  // Auth endpoints
  http.post(`${API_BASE_URL}/auth/login`, async ({ request }) => {
    const body = await request.json() as { email: string; password: string };
    
    if (body.email === 'demo@coredent.com' && body.password === 'demo123') {
      return HttpResponse.json({
        access_token: 'mock-access-token-123',
        refresh_token: 'mock-refresh-token-123',
        token_type: 'bearer',
        expires_in: 900,
        csrf_token: 'mock-csrf-token-123',
      });
    }
    
    return HttpResponse.json(
      { message: 'Invalid credentials' },
      { status: 401 }
    );
  }),

  http.get(`${API_BASE_URL}/auth/me`, () => {
    return HttpResponse.json({
      id: 'user-1',
      email: 'demo@coredent.com',
      firstName: 'Dr. Sarah',
      lastName: 'Johnson',
      role: 'dentist',
      practiceId: 'practice-1',
      practiceName: 'Bright Smile Dental',
    });
  }),
  http.post(`${API_BASE_URL}/auth/refresh`, async () => {
    return HttpResponse.json({
      access_token: 'mock-access-token-456',
      refresh_token: 'mock-refresh-token-456',
      token_type: 'bearer',
      expires_in: 900,
    });
  }),

  // Patients endpoints
  http.get(`${API_BASE_URL}/patients`, () => {
    return HttpResponse.json({
      data: [
        {
          id: 'patient-1',
          firstName: 'John',
          lastName: 'Doe',
          email: 'john.doe@example.com',
          phone: '555-0100',
          dateOfBirth: '1985-05-15',
          status: 'active' as const,
        } satisfies Patient,
      ],
      total: 1,
      page: 1,
      pageSize: 10,
    });
  }),

  http.get(`${API_BASE_URL}/patients/:id`, ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      firstName: 'John',
      lastName: 'Doe',
      email: 'john.doe@example.com',
      phone: '555-0100',
      dateOfBirth: '1985-05-15',
      status: 'active' as const,
    } satisfies Patient);
  }),

  // Appointments endpoints
  http.get(`${API_BASE_URL}/appointments`, () => {
    return HttpResponse.json([
      {
        id: 'apt-1',
        patientId: 'patient-1',
        patientName: 'John Doe',
        providerId: 'provider-1',
        providerName: 'Dr. Smith',
        type: 'cleaning' as const,
        status: 'scheduled' as const,
        startTime: new Date().toISOString(),
        endTime: new Date(Date.now() + 3600000).toISOString(),
        duration: 60,
      } satisfies Appointment,
    ]);
  }),

  // Clinic settings endpoints
  http.get(`${API_BASE_URL}/clinic/settings`, () => {
    return HttpResponse.json({
      id: 'clinic-1',
      name: 'Bright Smile Dental',
      email: 'info@brightsmile.com',
      phone: '555-0123',
      address: '123 Main Street',
      city: 'Springfield',
      state: 'IL',
      zipCode: '62701',
      country: 'USA',
      timezone: 'America/Chicago',
      currency: 'USD',
      logoUrl: null,
      workingHours: {
        monday: { enabled: true, start: '09:00', end: '17:00' },
        tuesday: { enabled: true, start: '09:00', end: '17:00' },
        wednesday: { enabled: true, start: '09:00', end: '17:00' },
        thursday: { enabled: true, start: '09:00', end: '17:00' },
        friday: { enabled: true, start: '09:00', end: '17:00' },
        saturday: { enabled: false, start: '09:00', end: '13:00' },
        sunday: { enabled: false, start: '09:00', end: '13:00' },
      },
      appointmentTypes: [
        {
          id: 'type-1',
          name: 'Cleaning',
          duration: 60,
          color: '#10b981',
          description: 'Regular dental cleaning',
          isActive: true,
        },
        {
          id: 'type-2',
          name: 'Exam',
          duration: 30,
          color: '#3b82f6',
          description: 'Dental examination',
          isActive: true,
        },
        {
          id: 'type-3',
          name: 'Filling',
          duration: 90,
          color: '#f59e0b',
          description: 'Dental filling procedure',
          isActive: true,
        },
      ],
      chairs: [
        {
          id: 'chair-1',
          name: 'Chair 1',
          isActive: true,
        },
        {
          id: 'chair-2',
          name: 'Chair 2',
          isActive: true,
        },
      ],
    });
  }),

  http.put(`${API_BASE_URL}/clinic/settings`, async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json(body);
  }),

  // Billing preferences endpoints
  http.get(`${API_BASE_URL}/settings/billing`, () => {
    return HttpResponse.json({
      taxRate: 0,
      currency: 'USD',
      paymentMethods: ['cash', 'card', 'insurance'],
      invoicePrefix: 'INV',
      invoiceStartNumber: 1000,
      paymentTerms: 'Payment due upon receipt',
      latePaymentFee: 0,
      reminderDays: [7, 3, 1],
      autoSendInvoices: true,
      autoSendReceipts: true,
      autoSendReminders: true,
    });
  }),

  http.put(`${API_BASE_URL}/settings/billing`, async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json(body);
  }),
];
