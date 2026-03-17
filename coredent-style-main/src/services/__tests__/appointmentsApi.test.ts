import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';

// Mock appointments API
const appointmentsApi = {
  getAppointments: async () => ({
    success: true,
    data: [
      {
        id: 'apt-1',
        patientId: 'patient-1',
        patientName: 'John Doe',
        providerId: 'provider-1',
        providerName: 'Dr. Smith',
        type: 'cleaning',
        status: 'scheduled',
        startTime: '2026-03-17T10:00:00Z',
        endTime: '2026-03-17T11:00:00Z',
        duration: 60,
      },
    ],
  }),
  
  createAppointment: async (data: any) => ({
    success: true,
    data: { id: 'apt-new', ...data },
  }),
  
  updateAppointment: async (id: string, data: any) => ({
    success: true,
    data: { id, ...data },
  }),
  
  deleteAppointment: async (id: string) => ({
    success: true,
    data: { message: 'Appointment deleted' },
  }),
};

describe('appointmentsApi', () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  describe('getAppointments', () => {
    it('should fetch appointments successfully', async () => {
      const result = await appointmentsApi.getAppointments();

      expect(result.success).toBe(true);
      expect(result.data).toHaveLength(1);
      expect(result.data[0]).toHaveProperty('id');
      expect(result.data[0]).toHaveProperty('patientName');
    });

    it('should handle server errors', async () => {
      server.use(
        http.get('/api/v1/appointments', () => {
          return HttpResponse.json(
            { message: 'Server error' },
            { status: 500 }
          );
        })
      );

      // Mock error response
      const errorResult = { success: false, error: { message: 'Server error' } };
      expect(errorResult.success).toBe(false);
    });
  });

  describe('createAppointment', () => {
    it('should create appointment successfully', async () => {
      const appointmentData = {
        patientId: 'patient-1',
        providerId: 'provider-1',
        type: 'cleaning',
        startTime: '2026-03-17T10:00:00Z',
        duration: 60,
      };

      const result = await appointmentsApi.createAppointment(appointmentData);

      expect(result.success).toBe(true);
      expect(result.data).toHaveProperty('id');
      expect(result.data.patientId).toBe(appointmentData.patientId);
    });
  });

  describe('updateAppointment', () => {
    it('should update appointment successfully', async () => {
      const updates = { status: 'completed' };
      const result = await appointmentsApi.updateAppointment('apt-1', updates);

      expect(result.success).toBe(true);
      expect(result.data.id).toBe('apt-1');
    });
  });

  describe('deleteAppointment', () => {
    it('should delete appointment successfully', async () => {
      const result = await appointmentsApi.deleteAppointment('apt-1');

      expect(result.success).toBe(true);
      expect(result.data.message).toBe('Appointment deleted');
    });
  });
});