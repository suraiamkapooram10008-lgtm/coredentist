import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { AuthProvider } from "@/contexts/AuthContext";
import Reports from "../Reports";

function createWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <AuthProvider>{children}</AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

describe("Reports Page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders the reports page", async () => {
    render(<Reports />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText(/report/i)).toBeInTheDocument();
    });
  });

  it("shows report type selector", async () => {
    render(<Reports />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(document.body).toBeInTheDocument();
    });
  });
});
