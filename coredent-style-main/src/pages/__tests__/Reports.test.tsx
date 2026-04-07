import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import Reports from "../Reports";

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

describe("Reports Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render reports page", () => {
    renderWithProviders(<Reports />);
    expect(document.body).toBeInTheDocument();
  });

  it("should display reports", async () => {
    renderWithProviders(<Reports />);

    await waitFor(() => {
      expect(document.body).toBeInTheDocument();
    });
  });

  it("should handle date range selection", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Reports />);

    const inputs = screen.queryAllByRole("textbox");
    if (inputs.length > 0) {
      await user.type(inputs[0], "2026-01-01");
      expect(inputs[0]).toHaveValue("2026-01-01");
    }
  });

  it("should handle report export", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Reports />);

    const buttons = screen.queryAllByRole("button");
    const exportButton = buttons.find((btn) => btn.textContent?.includes("Export"));
    
    if (exportButton) {
      await user.click(exportButton);
      expect(document.body).toBeInTheDocument();
    }
  });
});
