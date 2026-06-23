import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { AuthContext } from "@/contexts/auth-context";
import type { AuthContextValue } from "@/contexts/auth-context";
import Login from "../Login";

function createMockAuth(): AuthContextValue {
  return {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    role: null,
    login: vi.fn().mockResolvedValue(true),
    register: vi.fn().mockResolvedValue(true),
    logout: vi.fn().mockResolvedValue(undefined),
    hasRole: vi.fn().mockReturnValue(false),
  };
}

function renderLogin(auth?: AuthContextValue) {
  const mockAuth = auth || createMockAuth();
  return render(
    <BrowserRouter>
      <AuthContext.Provider value={mockAuth}>
        <Login />
      </AuthContext.Provider>
    </BrowserRouter>,
  );
}

describe("Login Page", () => {
  it("renders branding and form", () => {
    renderLogin();
    expect(screen.getByRole("heading", { level: 1, name: /coredent/i })).toBeInTheDocument();
    expect(screen.getByText(/welcome back/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("shows validation errors for empty submit", async () => {
    renderLogin();
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));
    // Zod validation fires synchronously
    expect(await screen.findByText(/valid email/i)).toBeInTheDocument();
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
  });

  it("has navigation links for forgot-password and register", () => {
    renderLogin();
    expect(screen.getByRole("link", { name: /forgot password/i })).toHaveAttribute(
      "href",
      "/forgot-password",
    );
    expect(screen.getByRole("link", { name: /create one/i })).toHaveAttribute(
      "href",
      "/register",
    );
  });
});
