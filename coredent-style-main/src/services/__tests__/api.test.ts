import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest';
import { server } from '@/test/mocks/server';
import { authApi, patientsApi, appointmentsApi } from '@/services/api';

// Start mock server
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('API Services', () => {
  describe('authApi', () => {
    it('logs in successfully with valid credentials', async () => {
      const response = await authApi.login({
        email: 'demo@coredent.com',
        password: 'demo123',
      });

      expect(response.success).toBe(true);
      expect(response.data).toBeDefined();
      expect(response.data?.access_token).toBeDefined();
      expect(response.data?.refresh_token).toBeDefined();
      expect(response.data?.csrf_token).toBeDefined();
    });

    it('fails login with invalid credentials', async () => {
      const response = await authApi.login({
        email: 'wrong@example.com',
        password: 'wrongpass',
      });

      expect(response.success).toBe(false);
      expect(response.error).toBeDefined();
    });

    it('gets current user', async () => {
      const response = await authApi.getCurrentUser();

      expect(response.success).toBe(true);
      expect(response.data).toBeDefined();
      expect(response.data?.email).toBe('demo@coredent.com');
    });
  });

  describe('patientsApi', () => {
    it('lists patients', async () => {
      const response = await patientsApi.list();

      expect(response.success).toBe(true);
      expect(response.data).toBeDefined();
      expect(Array.isArray(response.data?.data)).toBe(true);
    });

    it('gets patient by id', async () => {
      const response = await patientsApi.getById('patient-1');

      expect(response.success).toBe(true);
      expect(response.data).toBeDefined();
      expect(response.data?.id).toBe('patient-1');
    });
  });

  describe('appointmentsApi', () => {
    it('lists appointments', async () => {
      const response = await appointmentsApi.list({
        startDate: new Date().toISOString(),
        endDate: new Date().toISOString(),
      });

      expect(response.success).toBe(true);
      expect(response.data).toBeDefined();
      expect(Array.isArray(response.data)).toBe(true);
    });
  });
});
