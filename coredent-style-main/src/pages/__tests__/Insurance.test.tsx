import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { AuthProvider } from "@/contexts/AuthContext";
import Insurance from "../Insurance";

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

describe("Insurance Page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders the insurance page", async () => {
    render(<Insurance />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText(/insurance/i)).toBeInTheDocument();
    });
  });

  it("shows the search input", async () => {
    render(<Insurance />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
    });
  });
});
