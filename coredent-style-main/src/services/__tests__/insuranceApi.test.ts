import { describe, it, expect, beforeEach } from 'vitest';
import { insuranceApi } from '../insuranceApi';
import { server } from '@/test/mocks/server';
import { http, HttpResponse } from 'msw';
import type { InsuranceCarrier, PatientInsurance, InsuranceClaim } from '@/types/insurance';

const mockCarrier: InsuranceCarrier = {
  id: 'car-1',
  name: 'Delta Dental',
  payerId: 'DEL-001',
  phone: '800-555-0000',
  email: 'claims@delta.com',
  address: 'PO Box 1',
  city: 'Sacramento',
  state: 'CA',
  zipCode: '95814',
  isActive: true,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
};

const mockPolicy: PatientInsurance = {
  id: 'pol-1',
  patientId: 'p-1',
  carrierId: 'car-1',
  insuranceType: 'primary',
  policyNumber: 'POL-001',
  subscriberName: 'John Doe',
  subscriberId: 'SUB-001',
  relationshipToInsured: 'self',
  effectiveDate: '2026-01-01',
  coveragePercent: 80,
  createdAt: '2026-01-01T00:00:00Z',
  updatedAt: '2026-01-01T00:00:00Z',
};

const mockClaim: InsuranceClaim = {
  id: 'cl-1',
  patientId: 'p-1',
  patientName: 'John Doe',
  insuranceId: 'pol-1',
  claimNumber: 'CLM-001',
  serviceDate: '2026-06-01',
  procedures: [
    {
      procedureCode: 'D1110',
      description: 'Cleaning',
      quantity: 1,
      chargedAmount: 120,
      allowedAmount: 96,
      paidAmount: 0,
    },
  ],
  totalAmount: 120,
  status: 'draft',
  createdAt: '2026-06-01T00:00:00Z',
  updatedAt: '2026-06-01T00:00:00Z',
};

describe('insuranceApi', () => {
  beforeEach(() => server.resetHandlers());

  describe('carriers', () => {
    it('getCarriers returns a list of carriers', async () => {
      server.use(
        http.get('/api/v1/insurance/carriers', () =>
          HttpResponse.json({ carriers: [mockCarrier], count: 1 }),
        ),
      );
      const result = await insuranceApi.getCarriers();
      expect(result).toEqual([mockCarrier]);
    });

    it('getCarrier returns a single carrier', async () => {
      server.use(
        http.get('/api/v1/insurance/carriers/car-1', () => HttpResponse.json(mockCarrier)),
      );
      const result = await insuranceApi.getCarrier('car-1');
      expect(result).toEqual(mockCarrier);
    });

    it('createCarrier posts a new carrier', async () => {
      server.use(
        http.post('/api/v1/insurance/carriers', async ({ request }) => {
          const body = (await request.json()) as Record<string, unknown>;
          return HttpResponse.json({ ...mockCarrier, ...body, id: 'car-2' }, { status: 201 });
        }),
      );
      const result = await insuranceApi.createCarrier({
        name: 'Aetna',
        isActive: true,
      });
      expect(result.id).toBe('car-2');
    });

    it('updateCarrier sends a PUT', async () => {
      server.use(
        http.put('/api/v1/insurance/carriers/car-1', async ({ request }) => {
          const body = (await request.json()) as Record<string, unknown>;
          return HttpResponse.json({ ...mockCarrier, ...body });
        }),
      );
      const result = await insuranceApi.updateCarrier('car-1', { isActive: false });
      expect(result.isActive).toBe(false);
    });

    it('deleteCarrier resolves', async () => {
      server.use(
        http.delete('/api/v1/insurance/carriers/car-1', () =>
          HttpResponse.json({ message: 'Deleted' }),
        ),
      );
      await expect(insuranceApi.deleteCarrier('car-1')).resolves.toBeUndefined();
    });
  });

  describe('policies', () => {
    it('getPatientInsurance returns policies', async () => {
      server.use(
        http.get('/api/v1/insurance/patients/p-1/policies', () =>
          HttpResponse.json({ insurances: [mockPolicy], count: 1 }),
        ),
      );
      const result = await insuranceApi.getPatientInsurance('p-1');
      expect(result).toEqual([mockPolicy]);
    });

    it('getInsurancePolicy returns a single policy', async () => {
      server.use(
        http.get('/api/v1/insurance/policies/pol-1', () => HttpResponse.json(mockPolicy)),
      );
      const result = await insuranceApi.getInsurancePolicy('pol-1');
      expect(result).toEqual(mockPolicy);
    });

    it('addPatientInsurance posts a new policy', async () => {
      server.use(
        http.post('/api/v1/insurance/patients/p-1/policies', async ({ request }) => {
          const body = (await request.json()) as Record<string, unknown>;
          return HttpResponse.json({ ...mockPolicy, ...body, id: 'pol-2' }, { status: 201 });
        }),
      );
      const result = await insuranceApi.addPatientInsurance('p-1', {
        carrierId: 'car-1',
        insuranceType: 'primary',
        policyNumber: 'NEW-1',
        subscriberName: 'John Doe',
        subscriberId: 'SUB-1',
        relationshipToInsured: 'self',
        effectiveDate: '2026-01-01',
      });
      expect(result.id).toBe('pol-2');
    });

    it('updateInsurancePolicy sends a PUT', async () => {
      server.use(
        http.put('/api/v1/insurance/policies/pol-1', async ({ request }) => {
          const body = (await request.json()) as Record<string, unknown>;
          return HttpResponse.json({ ...mockPolicy, ...body });
        }),
      );
      const result = await insuranceApi.updateInsurancePolicy('pol-1', {
        coveragePercent: 90,
      });
      expect(result.coveragePercent).toBe(90);
    });

    it('deleteInsurancePolicy resolves', async () => {
      server.use(
        http.delete('/api/v1/insurance/policies/pol-1', () =>
          HttpResponse.json({ message: 'Deleted' }),
        ),
      );
      await expect(insuranceApi.deleteInsurancePolicy('pol-1')).resolves.toBeUndefined();
    });
  });

  describe('claims', () => {
    it('getClaims returns a list of claims', async () => {
      server.use(
        http.get('/api/v1/insurance/claims', () =>
          HttpResponse.json({ claims: [mockClaim], count: 1 }),
        ),
      );
      const result = await insuranceApi.getClaims();
      expect(result).toEqual([mockClaim]);
    });

    it('getClaim returns a single claim', async () => {
      server.use(
        http.get('/api/v1/insurance/claims/cl-1', () => HttpResponse.json(mockClaim)),
      );
      const result = await insuranceApi.getClaim('cl-1');
      expect(result).toEqual(mockClaim);
    });

    it('createClaim posts a new claim', async () => {
      server.use(
        http.post('/api/v1/insurance/claims', async ({ request }) => {
          const body = (await request.json()) as Record<string, unknown>;
          return HttpResponse.json({ ...mockClaim, ...body, id: 'cl-2' }, { status: 201 });
        }),
      );
      const result = await insuranceApi.createClaim({
        patientId: 'p-1',
        insuranceId: 'pol-1',
        serviceDate: '2026-06-01',
        procedures: [
          {
            procedureCode: 'D1110',
            description: 'Cleaning',
            quantity: 1,
            chargedAmount: 120,
          },
        ],
      });
      expect(result.id).toBe('cl-2');
    });

    it('updateClaim sends a PUT', async () => {
      server.use(
        http.put('/api/v1/insurance/claims/cl-1', async ({ request }) => {
          const body = (await request.json()) as Record<string, unknown>;
          return HttpResponse.json({ ...mockClaim, ...body });
        }),
      );
      const result = await insuranceApi.updateClaim('cl-1', { status: 'submitted' });
      expect(result.status).toBe('submitted');
    });

    it('submitClaim posts a submission request', async () => {
      server.use(
        http.post('/api/v1/insurance/claims/cl-1/submit', () =>
          HttpResponse.json({ ...mockClaim, status: 'submitted' }),
        ),
      );
      const result = await insuranceApi.submitClaim('cl-1');
      expect(result.status).toBe('submitted');
    });

    it('deleteClaim resolves', async () => {
      server.use(
        http.delete('/api/v1/insurance/claims/cl-1', () =>
          HttpResponse.json({ message: 'Deleted' }),
        ),
      );
      await expect(insuranceApi.deleteClaim('cl-1')).resolves.toBeUndefined();
    });
  });

  describe('pre-authorizations', () => {
    it('getPreAuthorizations returns the list', async () => {
      const preAuth = {
        id: 'pa-1',
        patientId: 'p-1',
        insuranceId: 'pol-1',
        status: 'pending' as const,
        requestedProcedures: ['D1110'],
        estimatedCost: 120,
        createdAt: '2026-06-01T00:00:00Z',
        updatedAt: '2026-06-01T00:00:00Z',
      };
      server.use(
        http.get('/api/v1/insurance/pre-auth', () =>
          HttpResponse.json({ pre_authorizations: [preAuth], count: 1 }),
        ),
      );
      const result = await insuranceApi.getPreAuthorizations();
      expect(result).toEqual([preAuth]);
    });

    it('getPreAuthorization returns a single pre-auth', async () => {
      const preAuth = {
        id: 'pa-1',
        patientId: 'p-1',
        insuranceId: 'pol-1',
        status: 'pending' as const,
        requestedProcedures: [],
        createdAt: '2026-06-01T00:00:00Z',
        updatedAt: '2026-06-01T00:00:00Z',
      };
      server.use(
        http.get('/api/v1/insurance/pre-auth/pa-1', () => HttpResponse.json(preAuth)),
      );
      const result = await insuranceApi.getPreAuthorization('pa-1');
      expect(result).toEqual(preAuth);
    });

    it('createPreAuthorization posts a new request', async () => {
      server.use(
        http.post('/api/v1/insurance/pre-auth', async ({ request }) => {
          const body = (await request.json()) as Record<string, unknown>;
          return HttpResponse.json(
            {
              id: 'pa-2',
              patientId: 'p-1',
              insuranceId: 'pol-1',
              status: 'pending',
              requestedProcedures: [],
              createdAt: '2026-06-01T00:00:00Z',
              updatedAt: '2026-06-01T00:00:00Z',
              ...body,
            },
            { status: 201 },
          );
        }),
      );
      const result = await insuranceApi.createPreAuthorization({
        patientId: 'p-1',
        insuranceId: 'pol-1',
        requestedProcedures: ['D1110'],
      });
      expect(result.id).toBe('pa-2');
    });

    it('updatePreAuthorization sends a PUT', async () => {
      const preAuth = {
        id: 'pa-1',
        patientId: 'p-1',
        insuranceId: 'pol-1',
        status: 'pending' as const,
        requestedProcedures: [],
        createdAt: '2026-06-01T00:00:00Z',
        updatedAt: '2026-06-01T00:00:00Z',
      };
      server.use(
        http.put('/api/v1/insurance/pre-auth/pa-1', async ({ request }) => {
          const body = (await request.json()) as Record<string, unknown>;
          return HttpResponse.json({ ...preAuth, ...body });
        }),
      );
      const result = await insuranceApi.updatePreAuthorization('pa-1', { status: 'approved' });
      expect(result.status).toBe('approved');
    });

    it('deletePreAuthorization resolves', async () => {
      server.use(
        http.delete('/api/v1/insurance/pre-auth/pa-1', () =>
          HttpResponse.json({ message: 'Deleted' }),
        ),
      );
      await expect(insuranceApi.deletePreAuthorization('pa-1')).resolves.toBeUndefined();
    });
  });

  describe('summary', () => {
    it('getSummary returns aggregated stats', async () => {
      server.use(
        http.get('/api/v1/insurance/summary', () =>
          HttpResponse.json({
            totalClaims: 100,
            pendingClaims: 4,
            approvedClaims: 50,
            rejectedClaims: 5,
            totalBilled: 12500,
            totalApproved: 9000,
            totalPaid: 7000,
            activePreAuths: 2,
          }),
        ),
      );
      const result = await insuranceApi.getSummary();
      expect(result.totalClaims).toBe(100);
    });
  });
});
