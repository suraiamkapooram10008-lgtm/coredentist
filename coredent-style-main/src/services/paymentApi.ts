/**
 * Payment API Service
 * Stripe integration for processing payments
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
