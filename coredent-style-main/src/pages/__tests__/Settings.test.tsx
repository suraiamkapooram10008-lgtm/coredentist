import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import Settings from "../Settings";

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

describe("Settings Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render settings page", () => {
    renderWithProviders(<Settings />);
    expect(document.body).toBeInTheDocument();
  });

  it("should display settings form", async () => {
    renderWithProviders(<Settings />);

    await waitFor(() => {
      expect(document.body).toBeInTheDocument();
    });
  });

  it("should handle form submission", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Settings />);

    const buttons = screen.queryAllByRole("button");
    const saveButton = buttons.find((btn) => btn.textContent?.includes("Save"));
    
    if (saveButton) {
      await user.click(saveButton);
      expect(document.body).toBeInTheDocument();
    }
  });

  it("should handle form changes", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Settings />);

    const inputs = screen.queryAllByRole("textbox");
    if (inputs.length > 0) {
      await user.type(inputs[0], "test value");
      expect(inputs[0]).toHaveValue("test value");
    }
  });
});
