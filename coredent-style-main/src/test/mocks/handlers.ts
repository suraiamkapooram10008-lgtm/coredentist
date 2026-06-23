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
          gender: 'male',
          address: {
            street: '123 Main St',
            city: 'Springfield',
            state: 'IL',
            zipCode: '62701',
          },
          emergencyContact: {
            name: 'Jane Doe',
            relationship: 'spouse',
            phone: '555-0101',
          },
          medicalAlerts: [],
          status: 'active',
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z',
        } satisfies Patient,
      ],
      total: 1,
      page: 1,
      limit: 10,
      totalPages: 1,
    });
  }),

  http.get(`${API_BASE_URL}/patients/:id`, ({ params }) => {
    return HttpResponse.json({
      id: String(params.id),
      firstName: 'John',
      lastName: 'Doe',
      email: 'john.doe@example.com',
      phone: '555-0100',
      dateOfBirth: '1985-05-15',
      gender: 'male',
      address: {
        street: '123 Main St',
        city: 'Springfield',
        state: 'IL',
        zipCode: '62701',
      },
      emergencyContact: {
        name: 'Jane Doe',
        relationship: 'spouse',
        phone: '555-0101',
      },
      medicalAlerts: [],
      status: 'active',
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
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
        operatoryId: 'chair-1',
        operatoryName: 'Chair 1',
        type: 'cleaning',
        status: 'scheduled',
        startTime: new Date().toISOString(),
        endTime: new Date(Date.now() + 3600000).toISOString(),
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
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

  // Billing summary & invoices
  http.get(`${API_BASE_URL}/billing/summary`, () => {
    return HttpResponse.json({
      totalRevenue: 45000,
      totalCollected: 40000,
      totalOutstanding: 5000,
      overdueAmount: 1200,
      invoicesCount: 120,
      paidCount: 100,
      pendingCount: 15,
      overdueCount: 5,
    });
  }),

  http.get(`${API_BASE_URL}/billing/invoices`, () => {
    return HttpResponse.json([]);
  }),

  http.get(`${API_BASE_URL}/invoices`, () => {
    return HttpResponse.json([]);
  }),

  // Reports dashboard
  http.get(`${API_BASE_URL}/reports/dashboard`, () => {
    return HttpResponse.json({
      appointments: {
        total: 60, completed: 45, cancelled: 10, noShow: 5,
        completionRate: 75, noShowRate: 8.3,
        byType: [{ type: 'checkup', count: 30 }],
        byDay: [{ date: '2026-06-01', appointments: 12 }],
      },
      revenue: {
        totalRevenue: 45000, totalCollected: 40000,
        totalOutstanding: 5000, averagePerVisit: 220,
        byMonth: [{ month: 'June', revenue: 45000, collected: 40000 }],
        byProcedure: [{ procedure: 'checkup', revenue: 15000 }],
      },
      treatmentAcceptance: {
        proposedPlans: 50, acceptedPlans: 40, completedPlans: 35,
        acceptanceRate: 80, completionRate: 87.5,
      },
      chairUtilization: {
        averageUtilization: 72, totalChairs: 4,
        peakHours: [{ hour: '10:00', utilization: 95 }],
        byChair: [{ chair: 'Chair 1', utilization: 80, appointments: 20 }],
        byDayOfWeek: [{ day: 'Monday', utilization: 85 }],
      },
    });
  }),

  // Communications endpoints
  http.get(`${API_BASE_URL}/communications/templates`, () => {
    return HttpResponse.json([]);
  }),

  http.get(`${API_BASE_URL}/communications/reminders`, () => {
    return HttpResponse.json([]);
  }),

  http.get(`${API_BASE_URL}/communications/conversations`, () => {
    return HttpResponse.json([]);
  }),

  http.get(`${API_BASE_URL}/communications/settings`, () => {
    return HttpResponse.json({
      unreadMessages: 0,
      messages: { totalSent: 0, deliveryRate: 0 },
      reminders: { pending: 0 },
    });
  }),

  // Insurance endpoints
  http.get(`${API_BASE_URL}/insurance/claims`, () => {
    return HttpResponse.json([]);
  }),

  http.get(`${API_BASE_URL}/insurance/carriers`, () => {
    return HttpResponse.json([]);
  }),

  // Treatment plans
  http.get(`${API_BASE_URL}/treatment-plans`, () => {
    return HttpResponse.json([]);
  }),

  // Subscriptions
  http.get(`${API_BASE_URL}/subscriptions/current`, () => {
    return HttpResponse.json(null);
  }),

  http.get(`${API_BASE_URL}/subscriptions/plans`, () => {
    return HttpResponse.json([]);
  }),

  http.get(`${API_BASE_URL}/subscriptions`, () => {
    return HttpResponse.json([]);
  }),

  http.get(`${API_BASE_URL}/subscriptions/stats`, () => {
    return HttpResponse.json(null);
  }),

  // Staff
  http.get(`${API_BASE_URL}/staff`, () => {
    return HttpResponse.json({ data: [], total: 0, page: 1, limit: 10, totalPages: 0 });
  }),

  http.get(`${API_BASE_URL}/staff/invitations`, () => {
    return HttpResponse.json([]);
  }),

  // Dental chart
  http.get(`${API_BASE_URL}/dental-chart/:patientId`, () => {
    return HttpResponse.json({ teeth: [], procedures: [] });
  }),

  // Imaging
  http.get(`${API_BASE_URL}/imaging/studies`, () => {
    return HttpResponse.json([]);
  }),

  // Automations
  http.get(`${API_BASE_URL}/automations`, () => {
    return HttpResponse.json([]);
  }),

  // Scheduling extras
  http.get(`${API_BASE_URL}/providers`, () => {
    return HttpResponse.json([]);
  }),

  http.get(`${API_BASE_URL}/chairs`, () => {
    return HttpResponse.json([]);
  }),

  http.get(`${API_BASE_URL}/appointment-types`, () => {
    return HttpResponse.json([]);
  }),
];
