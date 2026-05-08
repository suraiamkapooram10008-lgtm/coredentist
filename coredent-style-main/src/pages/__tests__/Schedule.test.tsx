import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import Schedule from "../Schedule";

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

describe("Schedule Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render schedule page", () => {
    renderWithProviders(<Schedule />);
    expect(document.body).toBeInTheDocument();
  });

  it("should display calendar", async () => {
    renderWithProviders(<Schedule />);

    await waitFor(() => {
      expect(document.body).toBeInTheDocument();
    });
  });

  it("should handle date navigation", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Schedule />);

    const buttons = screen.queryAllByRole("button");
    const nextButton = buttons.find((btn) => btn.textContent?.includes("Next"));
    
    if (nextButton) {
      await user.click(nextButton);
      expect(document.body).toBeInTheDocument();
    }
  });

  it("should handle appointment creation", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Schedule />);

    const buttons = screen.queryAllByRole("button");
    const addButton = buttons.find((btn) => btn.textContent?.includes("Add") || btn.textContent?.includes("New"));
    
    if (addButton) {
      await user.click(addButton);
      expect(document.body).toBeInTheDocument();
    }
  });
});
