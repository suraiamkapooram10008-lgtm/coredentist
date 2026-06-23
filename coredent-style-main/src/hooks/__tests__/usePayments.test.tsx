import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiClient } from "@/services/api";
import { usePaymentStats, useTransactions } from "../usePayments";

vi.mock("@/services/api", () => ({
  apiClient: { get: vi.fn() },
}));

const mockedGet = vi.mocked(apiClient.get);

function createWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
}

describe("usePayments", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("surfaces API failure instead of returning demo statistics", async () => {
    mockedGet.mockResolvedValue({
      success: false,
      error: { code: "UNAVAILABLE", message: "Payment service unavailable" },
    });

    const { result } = renderHook(() => usePaymentStats(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.data).toBeUndefined();
    expect(result.current.error).toEqual(new Error("Payment service unavailable"));
  });

  it("returns only transactions supplied by the API", async () => {
    const transaction = {
      id: "txn-1",
      patient: "Jamie Rivera",
      amount: 125,
      type: "Copay",
      method: "Card",
      status: "Completed" as const,
      date: "2026-06-20",
    };
    mockedGet.mockResolvedValue({
      success: true,
      data: { transactions: [transaction] },
    });

    const { result } = renderHook(() => useTransactions({ search: "Jamie" }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.data?.transactions).toEqual([transaction]);
    expect(mockedGet).toHaveBeenCalledWith("/payments/transactions", { search: "Jamie" });
  });
});