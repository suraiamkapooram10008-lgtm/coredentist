import { describe, it, expect, beforeEach } from 'vitest';
import { billingApi } from '../billingApi';
import { server } from '@/test/mocks/server';
import { http, HttpResponse } from 'msw';
import type { Invoice, BillingSummary } from '@/types/billing';

const mockInvoice: Invoice = {
  id: 'inv-1',
  invoiceNumber: 'INV-001',
  patientId: 'patient-1',
  patientName: 'John Doe',
  patientEmail: 'john@example.com',
  patientPhone: '555-0100',
  lineItems: [
    {
      id: 'li-1',
      procedureCode: 'D1110',
      description: 'Adult prophylaxis',
      quantity: 1,
      unitPrice: 120,
      discount: 0,
      total: 120,
    },
  ],
  subtotal: 120,
  taxRate: 0,
  taxAmount: 0,
  discountTotal: 0,
  total: 120,
  amountPaid: 0,
  balance: 120,
  status: 'draft',
  issueDate: '2026-06-01',
  dueDate: '2026-07-01',
  payments: [],
  notes: 'First visit',
  createdAt: '2026-06-01T00:00:00Z',
  updatedAt: '2026-06-01T00:00:00Z',
};

const mockSummary: BillingSummary = {
  totalOutstanding: 12000,
  totalPaidToday: 0,
  totalPaidThisMonth: 3400,
  overdueCount: 1,
  pendingCount: 3,
  pendingAmount: 3400,
};

describe('billingApi', () => {
  beforeEach(() => server.resetHandlers());

  describe('getInvoices', () => {
    it('returns invoice list', async () => {
      server.use(
        http.get('/api/v1/invoices', () => HttpResponse.json([mockInvoice])),
      );
      const result = await billingApi.getInvoices();
      expect(result).toEqual([mockInvoice]);
    });

    it('passes filter params', async () => {
      server.use(
        http.get('/api/v1/invoices', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('status')).toBe('paid');
          expect(url.searchParams.get('patientId')).toBe('p1');
          return HttpResponse.json([mockInvoice]);
        }),
      );
      await billingApi.getInvoices({ status: 'paid', patientId: 'p1' });
    });

    it('returns empty array when no invoices', async () => {
      server.use(http.get('/api/v1/invoices', () => HttpResponse.json([])));
      const result = await billingApi.getInvoices();
      expect(result).toEqual([]);
    });
  });

  describe('getInvoice', () => {
    it('returns a single invoice', async () => {
      server.use(
        http.get('/api/v1/invoices/inv-1', () => HttpResponse.json(mockInvoice)),
      );
      const result = await billingApi.getInvoice('inv-1');
      expect(result).toEqual(mockInvoice);
    });

    it('throws on 404', async () => {
      server.use(
        http.get('/api/v1/invoices/missing', () =>
          HttpResponse.json({ message: 'Not found' }, { status: 404 }),
        ),
      );
      await expect(billingApi.getInvoice('missing')).rejects.toThrow();
    });
  });

  describe('getSummary', () => {
    it('returns the billing summary', async () => {
      server.use(
        http.get('/api/v1/billing/summary', () => HttpResponse.json(mockSummary)),
      );
      const result = await billingApi.getSummary();
      expect(result.totalOutstanding).toBe(12000);
      expect(result.pendingCount).toBe(3);
    });
  });

  describe('createInvoice', () => {
    it('creates a new invoice and returns it', async () => {
      server.use(
        http.post('/api/v1/invoices', async ({ request }) => {
          const body = (await request.json()) as Record<string, unknown>;
          return HttpResponse.json({ ...mockInvoice, ...body, id: 'inv-2' }, { status: 201 });
        }),
      );
      const result = await billingApi.createInvoice({
        patientId: 'patient-1',
        patientName: 'New Patient',
        lineItems: [],
        dueDate: '2026-08-01',
      });
      expect(result.id).toBe('inv-2');
    });

    it('throws on a server error', async () => {
      server.use(
        http.post('/api/v1/invoices', () =>
          HttpResponse.json({ message: 'Bad data' }, { status: 422 }),
        ),
      );
      await expect(
        billingApi.createInvoice({
          patientId: 'p1',
          patientName: 'X',
          lineItems: [],
          dueDate: '2026-08-01',
        }),
      ).rejects.toThrow();
    });
  });

  describe('updateStatus', () => {
    it('sends a PUT and returns the updated invoice', async () => {
      server.use(
        http.put('/api/v1/invoices/inv-1/status', async ({ request }) => {
          const body = (await request.json()) as { status: string };
          return HttpResponse.json({ ...mockInvoice, status: body.status as Invoice['status'] });
        }),
      );
      const result = await billingApi.updateStatus('inv-1', 'sent');
      expect(result.status).toBe('sent');
    });
  });

  describe('recordPayment', () => {
    it('records a payment and returns the updated invoice', async () => {
      server.use(
        http.post('/api/v1/invoices/inv-1/payments', async ({ request }) => {
          const body = (await request.json()) as Record<string, unknown>;
          return HttpResponse.json({
            ...mockInvoice,
            payments: [
              {
                id: 'pay-1',
                date: '2026-06-22',
                amount: (body.amount as number) ?? 0,
                method: (body.method as string) ?? 'cash',
                reference: body.reference as string | undefined,
              },
            ],
            amountPaid: (body.amount as number) ?? 0,
            balance: 0,
            status: 'paid',
          });
        }),
      );
      const result = await billingApi.recordPayment('inv-1', {
        amount: 120,
        method: 'cash',
      });
      expect(result.status).toBe('paid');
      expect(result.payments).toHaveLength(1);
    });
  });

  describe('deleteInvoice', () => {
    it('deletes an invoice', async () => {
      server.use(
        http.delete('/api/v1/invoices/inv-1', () =>
          HttpResponse.json({ message: 'Deleted' }),
        ),
      );
      await expect(billingApi.deleteInvoice('inv-1')).resolves.toBeUndefined();
    });
  });

  describe('generateReceiptHTML', () => {
    it('produces a valid HTML document with the invoice number', () => {
      const html = billingApi.generateReceiptHTML(mockInvoice);
      expect(html).toContain('<!DOCTYPE html>');
      expect(html).toContain('INV-001');
      expect(html).toContain('John Doe');
      expect(html).toContain('D1110');
      expect(html).toContain('$120.00');
    });

    it('renders the PAID stamp when status is paid', () => {
      const html = billingApi.generateReceiptHTML({ ...mockInvoice, status: 'paid' });
      expect(html).toContain('✓ PAID IN FULL');
    });

    it('renders discount and tax lines when present', () => {
      const html = billingApi.generateReceiptHTML({
        ...mockInvoice,
        discountTotal: 10,
        taxRate: 8,
        taxAmount: 9.6,
        total: 119.6,
        balance: 119.6,
      });
      expect(html).toContain('Discounts:');
      expect(html).toContain('Tax (8%):');
    });

    it('renders payment history when payments exist', () => {
      const html = billingApi.generateReceiptHTML({
        ...mockInvoice,
        status: 'paid',
        payments: [
          { id: 'p1', date: '2026-06-22', amount: 120, method: 'credit_card' },
        ],
      });
      expect(html).toContain('Payment History');
      expect(html).toContain('credit card');
    });
  });
});
