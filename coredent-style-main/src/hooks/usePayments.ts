// ============================================
// CoreDent PMS - usePayments Hook
// ============================================

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/services/api";
import type { ApiResponse } from "@/types/api";

export interface PaymentStats {
  todayRevenue: number;
  todayTransactions: number;
  monthRevenue: number;
  monthGrowth: number;
  pendingPayments: number;
  pendingCount: number;
  recurringRevenue: number;
}

export interface Transaction {
  id: string;
  patient: string;
  amount: number;
  type: string;
  method: string;
  status: "Completed" | "Pending" | "Failed";
  date: string;
}

export interface RecurringPlan {
  id: string;
  patient: string;
  plan: string;
  amount: number;
  frequency: string;
  nextDate: string;
  status: "Active" | "Cancelled" | "Pending";
}

export interface Terminal {
  id: string;
  name: string;
  status: "Online" | "Offline";
  location: string;
  lastTransaction: string;
}

function requirePaymentData<T>(response: ApiResponse<T>, resource: string): ApiResponse<T> {
  if (response.success && response.data !== undefined) {
    return response;
  }

  throw new Error(response.error?.message || `Unable to load ${resource}`);
}

export function usePaymentStats() {
  return useQuery({
    queryKey: ["payments", "stats"],
    queryFn: async () => requirePaymentData(
      await apiClient.get<PaymentStats>("/payments/stats"),
      "payment statistics",
    ),
    staleTime: 5 * 60 * 1000,
  });
}

export function useTransactions(filters?: { search?: string }) {
  return useQuery({
    queryKey: ["payments", "transactions", filters],
    queryFn: async () => requirePaymentData(
      await apiClient.get<{ transactions: Transaction[] }>(
        "/payments/transactions",
        filters as Record<string, unknown>,
      ),
      "payment transactions",
    ),
    staleTime: 2 * 60 * 1000,
  });
}

export function useRecurringPlans() {
  return useQuery({
    queryKey: ["payments", "plans"],
    queryFn: async () => requirePaymentData(
      await apiClient.get<{ plans: RecurringPlan[] }>("/payments/plans"),
      "recurring payment plans",
    ),
    staleTime: 5 * 60 * 1000,
  });
}

export function useTerminals() {
  return useQuery({
    queryKey: ["payments", "terminals"],
    queryFn: async () => requirePaymentData(
      await apiClient.get<{ terminals: Terminal[] }>("/payments/terminals"),
      "payment terminals",
    ),
    staleTime: 5 * 60 * 1000,
  });
}