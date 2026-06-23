import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { AuthContext } from "@/contexts/auth-context";
import type { AuthContextValue } from "@/contexts/auth-context";
import Register from "../Register";

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

describe("Register Page", () => {
  it("renders branding and registration form", () => {
    render(
      <BrowserRouter>
        <AuthContext.Provider value={createMockAuth()}>
          <Register />
        </AuthContext.Provider>
      </BrowserRouter>,
    );
    expect(screen.getByRole("heading", { level: 1, name: /coredent/i })).toBeInTheDocument();
    expect(screen.getByText(/get started with coredent/i)).toBeInTheDocument();
  });

  it("has form fields for practice and user info", () => {
    render(
      <BrowserRouter>
        <AuthContext.Provider value={createMockAuth()}>
          <Register />
        </AuthContext.Provider>
      </BrowserRouter>,
    );
    expect(screen.getByLabelText(/practice name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/first name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it("links back to login page", () => {
    render(
      <BrowserRouter>
        <AuthContext.Provider value={createMockAuth()}>
          <Register />
        </AuthContext.Provider>
      </BrowserRouter>,
    );
    const loginLink = screen.getByRole("link", { name: /sign in/i });
    expect(loginLink).toHaveAttribute("href", "/login");
  });
});
