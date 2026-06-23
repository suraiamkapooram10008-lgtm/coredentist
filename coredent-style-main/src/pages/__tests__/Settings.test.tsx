import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { AuthProvider } from "@/contexts/AuthContext";
import Settings from "../Settings";

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

describe("Settings Page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders the settings heading", async () => {
    render(<Settings />, { wrapper: createWrapper() });
    // Heading is visible even during loading
    expect(
      screen.getByRole("heading", { level: 1, name: /settings/i }),
    ).toBeInTheDocument();
  });

  it("loads and shows tab navigation", async () => {
    render(<Settings />, { wrapper: createWrapper() });
    await waitFor(() => {
      // After loading, the tabs should be visible
      expect(screen.getByRole("tab", { name: /clinic/i })).toBeInTheDocument();
    });
    expect(screen.getByRole("tab", { name: /staff/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /appointments/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /billing/i })).toBeInTheDocument();
  });
});
