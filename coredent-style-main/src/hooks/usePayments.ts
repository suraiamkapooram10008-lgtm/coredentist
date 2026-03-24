/**
 * Payment Hooks
 * React Query hooks for payment operations
 * 
 * Design decisions:
 * - Source of truth: Server (React Query manages cache)
 * - Derived: Payment status derived from API response
 * - User actions: Triggered via mutations
 * 
 * Why no useEffect:
 * - useQuery handles data fetching with automatic caching
 * - Mutations are user-triggered actions
 * - React Query manages loading/error states declaratively
 */

import { useMutation, useQuery } from '@tanstack/react-query';
import {
  createPaymentIntent,
  listPaymentMethods,
  refundPayment,
  getPaymentStatus,
  type PaymentIntentCreate,
} from '@/services/paymentApi';

/**
 * Hook to create a Stripe PaymentIntent
 * 
 * Usage:
 * ```tsx
 * const { mutate: createIntent, isPending } = useCreatePaymentIntent({
 *   onSuccess: (data) => {
 *     // Redirect to Stripe checkout or open payment modal
 *   }
 * });
 * 
 * createIntent({ invoice_id: '123', amount: 100 });
 * ```
 */
export const useCreatePaymentIntent = (options?: {
  onSuccess?: (data: Awaited<ReturnType<typeof createPaymentIntent>>) => void;
  onError?: (error: Error) => void;
}) => {
  return useMutation({
    mutationFn: (data: PaymentIntentCreate) => createPaymentIntent(data),
    onSuccess: options?.onSuccess,
    onError: options?.onError,
  });
};

/**
 * Hook to get available payment methods
 * 
 * Usage:
 * ```tsx
 * const { data, isLoading } = usePaymentMethods();
 * 
 * if (data?.data?.methods) {
 *   // Render payment methods
 * }
 * ```
 */
export const usePaymentMethods = () => {
  return useQuery({
    queryKey: ['paymentMethods'],
    queryFn: () => listPaymentMethods(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
  });
};

/**
 * Hook to process a refund
 * 
 * Usage:
 * ```tsx
 * const { mutate: processRefund, isPending } = useRefundPayment({
 *   onSuccess: () => toast.success('Refund processed')
 * });
 * 
 * processRefund({ transactionId: 'tx_123', amount: 50 });
 * ```
 */
export const useRefundPayment = (options?: {
  onSuccess?: () => void;
  onError?: (error: Error) => void;
}) => {
  return useMutation({
    mutationFn: ({ transactionId, amount }: { transactionId: string; amount?: number }) =>
      refundPayment(transactionId, amount),
    onSuccess: options?.onSuccess,
    onError: options?.onError,
  });
};

/**
 * Hook to get payment status for an invoice
 * 
 * Usage:
 * ```tsx
 * const { data, refetch } = usePaymentStatus('invoice-123');
 * ```
 */
export const usePaymentStatus = (invoiceId: string) => {
  return useQuery({
    queryKey: ['paymentStatus', invoiceId],
    queryFn: () => getPaymentStatus(invoiceId),
    enabled: !!invoiceId,
    staleTime: 30 * 1000, // 30 seconds for payment status
    refetchInterval: (query) => {
      // Poll every 5 seconds if payment is pending
      const status = query.state.data?.data?.status;
      return status === 'pending' ? 5000 : false;
    },
  });
};
