import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { AuthProvider } from "@/contexts/AuthContext";
import TreatmentPlans from "../TreatmentPlans";

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

describe("TreatmentPlans Page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders the page heading and search input", async () => {
    render(<TreatmentPlans />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { level: 1, name: /treatment plans/i }),
      ).toBeInTheDocument();
    });
    expect(screen.getByPlaceholderText(/search plans/i)).toBeInTheDocument();
  });

  it("shows empty state and create plan CTA when no plans exist", async () => {
    render(<TreatmentPlans />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText(/no treatment plans found/i)).toBeInTheDocument();
    });
    // "New Plan" button in header + "Create Plan" in empty state
    const createButtons = screen.getAllByRole("button", { name: /plan/i });
    expect(createButtons.length).toBeGreaterThanOrEqual(1);
  });
});
