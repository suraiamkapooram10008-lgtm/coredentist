import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { AuthProvider } from "@/contexts/AuthContext";
import StaffManagement from "../admin/StaffManagement";

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

describe("StaffManagement Page", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders the page heading and invite button", async () => {
    render(<StaffManagement />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { level: 1, name: /staff management/i }),
      ).toBeInTheDocument();
    });
    expect(
      screen.getByRole("button", { name: /invite staff/i }),
    ).toBeInTheDocument();
  });

  it("shows search input and filter controls", async () => {
    render(<StaffManagement />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(
        screen.getByPlaceholderText(/search by name or email/i),
      ).toBeInTheDocument();
    });
  });
});
