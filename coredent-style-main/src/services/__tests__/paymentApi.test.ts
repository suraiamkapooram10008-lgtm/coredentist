import { describe, it, expect, beforeEach } from 'vitest';
import { createRazorpayOrder, verifyRazorpayPayment } from '../paymentApi';
import { server } from '@/test/mocks/server';
import { http, HttpResponse } from 'msw';

describe('paymentApi', () => {
  beforeEach(() => server.resetHandlers());

  describe('createRazorpayOrder', () => {
    it('returns order details', async () => {
      server.use(
        http.post('/api/v1/payments/razorpay/order', () =>
          HttpResponse.json({
            key_id: 'rzp_test_1',
            amount: 12000,
            currency: 'INR',
            order_id: 'order_1',
            receipt: 'rcpt_1',
          }),
        ),
      );
      const result = await createRazorpayOrder({
        invoice_id: 'inv-1',
        amount: 12000,
        currency: 'INR',
        receipt: 'rcpt_1',
      });
      expect(result.data?.order_id).toBe('order_1');
      expect(result.data?.amount).toBe(12000);
    });
  });

  describe('verifyRazorpayPayment', () => {
    it('returns verification result', async () => {
      server.use(
        http.post('/api/v1/payments/razorpay/verify', () =>
          HttpResponse.json({ payment_id: 'pay_1', verified: true }),
        ),
      );
      const result = await verifyRazorpayPayment({
        razorpay_order_id: 'order_1',
        razorpay_payment_id: 'pay_1',
        razorpay_signature: 'sig',
        invoice_id: 'inv-1',
      });
      expect(result.data?.verified).toBe(true);
      expect(result.data?.payment_id).toBe('pay_1');
    });

    it('surfaces a 400 signature verification failure', async () => {
      server.use(
        http.post('/api/v1/payments/razorpay/verify', () =>
          HttpResponse.json(
            { message: 'Invalid signature' },
            { status: 400 },
          ),
        ),
      );
      const result = await verifyRazorpayPayment({
        razorpay_order_id: 'order_1',
        razorpay_payment_id: 'pay_1',
        razorpay_signature: 'bad',
        invoice_id: 'inv-1',
      });
      expect(result.success).toBe(false);
    });
  });
});
