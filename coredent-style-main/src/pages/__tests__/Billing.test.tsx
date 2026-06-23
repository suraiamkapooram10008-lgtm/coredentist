import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { AuthProvider } from "@/contexts/AuthContext";
import Billing from "../Billing";

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

describe("Billing Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the billing page", async () => {
    render(<Billing />, { wrapper: createWrapper() });
    // The page renders immediately with its header and stat cards.
    await waitFor(() => {
      expect(screen.getByText(/New Invoice/i)).toBeInTheDocument();
    });
  });

  it("shows the search input", async () => {
    render(<Billing />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
    });
  });
});
