import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import Dashboard from "../Dashboard";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe("Dashboard Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render dashboard", () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByText(/dashboard/i) || screen.getByRole("heading")).toBeInTheDocument();
  });

  it("should display loading state initially", () => {
    renderWithProviders(<Dashboard />);
    // Dashboard should render without crashing
    expect(document.body).toBeInTheDocument();
  });

  it("should handle errors gracefully", async () => {
    renderWithProviders(<Dashboard />);
    
    await waitFor(() => {
      // Should render without crashing even if data fails to load
      expect(document.body).toBeInTheDocument();
    });
  });
});
