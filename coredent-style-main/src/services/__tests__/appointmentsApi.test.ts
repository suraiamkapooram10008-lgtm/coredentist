import { describe, it, expect, beforeEach } from 'vitest';
import {
  listAppointments,
  getAppointment,
  createAppointment,
  updateAppointment,
  deleteAppointment,
  getAppointmentStats,
  listAppointmentTypes,
  sendAppointmentReminder,
} from '../appointmentsApi';
import { server } from '@/test/mocks/server';
import { http, HttpResponse } from 'msw';
import type { Appointment } from '../appointmentsApi';

const mockAppointment: Appointment = {
  id: 'apt-1',
  patient: 'p-1',
  patientName: 'John Doe',
  time: '09:00',
  duration: '60',
  type: 'cleaning',
  dentist: 'Dr. Smith',
  status: 'Confirmed',
  date: '2026-06-22',
};

describe('appointmentsApi', () => {
  beforeEach(() => server.resetHandlers());

  it('listAppointments returns appointments', async () => {
    server.use(
      http.get('/api/v1/appointments', () =>
        HttpResponse.json({ appointments: [mockAppointment], total: 1 }),
      ),
    );
    const result = await listAppointments();
    expect(result.success).toBe(true);
    expect(result.data?.appointments).toEqual([mockAppointment]);
  });

  it('listAppointments passes filter params', async () => {
    server.use(
      http.get('/api/v1/appointments', ({ request }) => {
        const url = new URL(request.url);
        expect(url.searchParams.get('status')).toBe('Confirmed');
        return HttpResponse.json({ appointments: [], total: 0 });
      }),
    );
    await listAppointments({ status: 'Confirmed' });
  });

  it('getAppointment returns a single appointment', async () => {
    server.use(
      http.get('/api/v1/appointments/apt-1', () => HttpResponse.json(mockAppointment)),
    );
    const result = await getAppointment('apt-1');
    expect(result.data).toEqual(mockAppointment);
  });

  it('createAppointment posts a new appointment', async () => {
    server.use(
      http.post('/api/v1/appointments', async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ ...mockAppointment, ...body, id: 'apt-2' }, { status: 201 });
      }),
    );
    const result = await createAppointment({ ...mockAppointment });
    expect(result.data?.id).toBe('apt-2');
  });

  it('updateAppointment sends a PUT', async () => {
    server.use(
      http.put('/api/v1/appointments/apt-1', async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ ...mockAppointment, ...body });
      }),
    );
    const result = await updateAppointment('apt-1', { status: 'Cancelled' });
    expect(result.data?.status).toBe('Cancelled');
  });

  it('deleteAppointment removes an appointment', async () => {
    server.use(
      http.delete('/api/v1/appointments/apt-1', () =>
        HttpResponse.json({ message: 'Deleted' }),
      ),
    );
    const result = await deleteAppointment('apt-1');
    expect(result.success).toBe(true);
  });

  it('getAppointmentStats returns stats', async () => {
    server.use(
      http.get('/api/v1/appointments/stats', () =>
        HttpResponse.json({
          todayAppointments: 5,
          confirmed: 3,
          pending: 2,
          cancelled: 0,
        }),
      ),
    );
    const result = await getAppointmentStats();
    expect(result.data?.todayAppointments).toBe(5);
  });

  it('listAppointmentTypes returns types', async () => {
    server.use(
      http.get('/api/v1/appointments/types', () =>
        HttpResponse.json({
          types: [
            { id: 't-1', name: 'Cleaning', duration: 30 },
            { id: 't-2', name: 'Root Canal', duration: 90 },
          ],
        }),
      ),
    );
    const result = await listAppointmentTypes();
    expect(result.data?.types).toHaveLength(2);
  });

  it('sendAppointmentReminder posts the request', async () => {
    server.use(
      http.post('/api/v1/appointments/apt-1/reminder', () =>
        HttpResponse.json({ message: 'Reminder sent' }),
      ),
    );
    const result = await sendAppointmentReminder('apt-1');
    expect(result.data?.message).toBe('Reminder sent');
  });
});
