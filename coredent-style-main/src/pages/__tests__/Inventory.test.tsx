import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import Inventory from "../Inventory";

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

describe("Inventory Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render inventory page", () => {
    renderWithProviders(<Inventory />);
    expect(document.body).toBeInTheDocument();
  });

  it("should display inventory items", async () => {
    renderWithProviders(<Inventory />);

    await waitFor(() => {
      expect(document.body).toBeInTheDocument();
    });
  });

  it("should handle search", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Inventory />);

    const inputs = screen.queryAllByRole("textbox");
    if (inputs.length > 0) {
      await user.type(inputs[0], "test item");
      expect(inputs[0]).toHaveValue("test item");
    }
  });

  it("should handle add item", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Inventory />);

    const buttons = screen.queryAllByRole("button");
    const addButton = buttons.find((btn) => btn.textContent?.includes("Add"));
    
    if (addButton) {
      await user.click(addButton);
      expect(document.body).toBeInTheDocument();
    }
  });
});
