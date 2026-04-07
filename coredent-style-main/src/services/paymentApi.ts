/**
 * Payment API Service
 * Stripe (US) and Razorpay (India - UPI/Paytm/PhonePe) integration
 * 
 * Design decisions:
 * - Uses React Query for server state management
 * - No useEffect - React Query handles caching and refetching
 * - Type-safe API responses
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';

// ============================================
// Types
// ============================================

export interface PaymentIntentCreate {
  invoice_id: string;
  amount?: number;
}

export interface PaymentIntentResponse {
  client_secret: string;
  payment_intent_id: string;
  amount: number;
  currency: string;
}

export interface PaymentMethod {
  id: string;
  type: string;
  enabled: boolean;
}

export interface RefundRequest {
  transaction_id: string;
  amount?: number;
}

export interface RefundResponse {
  refund_id: string;
  amount: number;
  status: string;
}

// ============================================
// API Functions (for use with React Query)
// ============================================

/**
 * Create a Stripe PaymentIntent for an invoice
 * Source of truth: Stripe API
 * Stored: Invoice status in database
 */
export const createPaymentIntent = async (
  data: PaymentIntentCreate
): Promise<ApiResponse<PaymentIntentResponse>> => {
  return apiClient.post<PaymentIntentResponse>('/payments/create-payment-intent', data);
};

/**
 * List available payment methods
 */
export const listPaymentMethods = async (): Promise<ApiResponse<{ methods: PaymentMethod[] }>> => {
  return apiClient.get<{ methods: PaymentMethod[] }>('/payments/methods');
};

/**
 * Process a refund for a payment
 */
export const refundPayment = async (
  transactionId: string,
  amount?: number
): Promise<ApiResponse<RefundResponse>> => {
  const params = new URLSearchParams({ transaction_id: transactionId });
  if (amount) {
    params.append('amount', amount.toString());
  }
  return apiClient.post<RefundResponse>(`/payments/refund?${params}`, {});
};

/**
 * Get payment status for an invoice
 * Note: This would typically be handled via webhook
 */
export const getPaymentStatus = async (
  invoiceId: string
): Promise<ApiResponse<{ status: string; last_payment_id?: string }>> => {
  return apiClient.get<{ status: string; last_payment_id?: string }>(`/payments/status/${invoiceId}`);
};

// ============================================
// Razorpay Types (Indian Market - UPI/Paytm/PhonePe)
// ============================================

export interface RazorpayOrderCreate {
  invoice_id: string;
  amount?: number;
  currency?: string;
  receipt?: string;
}

export interface RazorpayOrderResponse {
  order_id: string;
  amount: number;
  currency: string;
  receipt: string;
  key_id: string;
  status: string;
}

export interface RazorpayPaymentVerify {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
  invoice_id: string;
}

export interface RazorpayPaymentResponse {
  payment_id: string;
  order_id: string;
  amount: number;
  currency: string;
  status: string;
  method: string; // upi, card, netbanking, wallet
}

export interface RazorpayRefundRequest {
  payment_id: string;
  amount?: number;
}

export interface RazorpayRefundResponse {
  refund_id: string;
  amount: number;
  status: string;
}

// ============================================
// Razorpay API Functions
// ============================================

/**
 * Create a Razorpay Order for Indian payments
 * Supports: UPI (GPay, PhonePe, Paytm), Cards, Net Banking, Wallets
 */
export const createRazorpayOrder = async (
  data: RazorpayOrderCreate
): Promise<ApiResponse<RazorpayOrderResponse>> => {
  return apiClient.post<RazorpayOrderResponse>('/payments/razorpay/create-order', data);
};

/**
 * Verify a Razorpay payment signature and update invoice
 */
export const verifyRazorpayPayment = async (
  data: RazorpayPaymentVerify
): Promise<ApiResponse<RazorpayPaymentResponse>> => {
  return apiClient.post<RazorpayPaymentResponse>('/payments/razorpay/verify-payment', data);
};

/**
 * Process a refund for a Razorpay payment
 */
export const refundRazorpayPayment = async (
  data: RazorpayRefundRequest
): Promise<ApiResponse<RazorpayRefundResponse>> => {
  return apiClient.post<RazorpayRefundResponse>('/payments/razorpay/refund', data);
};

/**
 * Load Razorpay SDK script dynamically
 */
export const loadRazorpayScript = (): Promise<boolean> => {
  return new Promise((resolve) => {
    if (document.getElementById('razorpay-sdk')) {
      resolve(true);
      return;
    }
    const script = document.createElement('script');
    script.id = 'razorpay-sdk';
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
};

// ============================================
// React Query Hooks (to be created in hooks folder)
// ============================================

/**
 * useCreatePaymentIntent hook
 * Returns a mutation for creating payment intents
 * 
 * Why no useEffect:
 * - React Query handles caching automatically
 * - Mutations are user-triggered actions
 * - No need for effect-based data loading
 */
// To be added to hooks/usePayments.ts:
// import { useMutation } from '@tanstack/react-query';
// 
// export const useCreatePaymentIntent = () => {
//   return useMutation({
//     mutationFn: createPaymentIntent,
//     onSuccess: (data) => {
//       // Handle success - e.g., redirect to payment page
//     },
//     onError: (error) => {
//       // Handle error - e.g., show toast
//     },
//   });
// };

/**
 * usePaymentMethods hook
 * Returns a query for fetching available payment methods
 * 
 * Why no useEffect:
 * - useQuery handles fetching and caching
 * - Component declares its data requirements declaratively
 * - React Query manages background refetching
 */
// To be added to hooks/usePayments.ts:
// import { useQuery } from '@tanstack/react-query';
// 
// export const usePaymentMethods = () => {
//   return useQuery({
//     queryKey: ['paymentMethods'],
//     queryFn: listPaymentMethods,
//     staleTime: 5 * 60 * 1000, // 5 minutes
//   });
// };
