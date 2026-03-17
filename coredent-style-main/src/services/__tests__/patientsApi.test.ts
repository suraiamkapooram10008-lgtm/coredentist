import { describe, it, expect, beforeEach } from 'vitest';
import { patientsApi } from '../api';
import { server } from '@/test/mocks/server';
import { http, HttpResponse } from 'msw';

describe('patientsApi', () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  const mockPatient = {
    id: 'patient-1',
    firstName: 'John',
    lastName: 'Doe',
    email: 'john.doe@example.com',
    phone: '+1234567890',
    dateOfBirth: '1990-01-01',
    address: '123 Main St, City, State 12345',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  };

  describe('list', () => {
    it('should fetch patients list successfully', async () => {
      const mockResponse = {
        data: [mockPatient],
        total: 1,
        page: 1,
        pageSize: 10,
        totalPages: 1,
      };

      server.use(
        http.get('/api/v1/patients', () => {
          return HttpResponse.json(mockResponse);
        })
      );

      const result = await patientsApi.list();

      expect(result.success).toBe(true);
      expect(result.data).toEqual(mockResponse);
    });

    it('should handle search parameters', async () => {
      const mockResponse = {
        data: [mockPatient],
        total: 1,
        page: 1,
        pageSize: 10,
        totalPages: 1,
      };

      server.use(
        http.get('/api/v1/patients', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('search')).toBe('John');
          expect(url.searchParams.get('page')).toBe('1');
          return HttpResponse.json(mockResponse);
        })
      );

      const result = await patientsApi.list({
        search: 'John',
        page: 1,
        pageSize: 10,
      });

      expect(result.success).toBe(true);
    });
  });

  describe('getById', () => {
    it('should fetch patient by ID successfully', async () => {
      server.use(
        http.get('/api/v1/patients/patient-1', () => {
          return HttpResponse.json(mockPatient);
        })
      );

      const result = await patientsApi.getById('patient-1');

      expect(result.success).toBe(true);
      expect(result.data).toEqual(mockPatient);
    });

    it('should handle patient not found', async () => {
      server.use(
        http.get('/api/v1/patients/nonexistent', () => {
          return HttpResponse.json(
            { message: 'Patient not found' },
            { status: 404 }
          );
        })
      );

      const result = await patientsApi.getById('nonexistent');

      expect(result.success).toBe(false);
      expect(result.error?.message).toBe('Patient not found');
    });
  });

  describe('create', () => {
    it('should create patient successfully', async () => {
      const newPatient = {
        firstName: 'Jane',
        lastName: 'Smith',
        email: 'jane.smith@example.com',
        phone: '+1987654321',
        dateOfBirth: '1985-05-15',
        address: '456 Oak Ave, City, State 54321',
      };

      const createdPatient = {
        ...newPatient,
        id: 'patient-2',
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      };

      server.use(
        http.post('/api/v1/patients', async ({ request }) => {
          const body = await request.json();
          expect(body).toEqual(newPatient);
          return HttpResponse.json(createdPatient, { status: 201 });
        })
      );

      const result = await patientsApi.create(newPatient);

      expect(result.success).toBe(true);
      expect(result.data).toEqual(createdPatient);
    });

    it('should handle validation errors', async () => {
      server.use(
        http.post('/api/v1/patients', () => {
          return HttpResponse.json(
            { 
              message: 'Validation error',
              details: ['Email is required', 'Phone is invalid']
            },
            { status: 422 }
          );
        })
      );

      const result = await patientsApi.create({
        firstName: 'Test',
        lastName: 'User',
      } as any);

      expect(result.success).toBe(false);
      expect(result.error?.message).toBe('Validation error');
    });
  });

  describe('update', () => {
    it('should update patient successfully', async () => {
      const updates = {
        phone: '+1111111111',
        address: '789 Pine St, City, State 67890',
      };

      const updatedPatient = {
        ...mockPatient,
        ...updates,
        updatedAt: '2024-01-02T00:00:00Z',
      };

      server.use(
        http.put('/api/v1/patients/patient-1', async ({ request }) => {
          const body = await request.json();
          expect(body).toEqual(updates);
          return HttpResponse.json(updatedPatient);
        })
      );

      const result = await patientsApi.update('patient-1', updates);

      expect(result.success).toBe(true);
      expect(result.data).toEqual(updatedPatient);
    });
  });

  describe('delete', () => {
    it('should delete patient successfully', async () => {
      server.use(
        http.delete('/api/v1/patients/patient-1', () => {
          return HttpResponse.json({ message: 'Patient deleted successfully' });
        })
      );

      const result = await patientsApi.delete('patient-1');

      expect(result.success).toBe(true);
    });

    it('should handle delete errors', async () => {
      server.use(
        http.delete('/api/v1/patients/patient-1', () => {
          return HttpResponse.json(
            { message: 'Cannot delete patient with active appointments' },
            { status: 409 }
          );
        })
      );

      const result = await patientsApi.delete('patient-1');

      expect(result.success).toBe(false);
      expect(result.error?.message).toBe('Cannot delete patient with active appointments');
    });
  });
});