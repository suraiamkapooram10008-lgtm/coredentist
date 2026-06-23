import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ProtectedRoute } from "../ProtectedRoute";
import { useAuth } from "@/contexts/auth-context";
import type { AuthContextValue } from "@/contexts/auth-context";
import type { UserRole } from "@/types/api";

vi.mock("@/contexts/auth-context", () => ({
  useAuth: vi.fn(),
}));

const mockedUseAuth = vi.mocked(useAuth);
const baseAuth: Pick<AuthContextValue, "login" | "register" | "logout" | "hasRole"> = {
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  hasRole: vi.fn(),
};

function renderRoute(roles?: UserRole[]) {
  return render(
    <MemoryRouter initialEntries={["/private"]}>
      <Routes>
        <Route path="/login" element={<div>Login page</div>} />
        <Route
          path="/private"
          element={
            <ProtectedRoute roles={roles}>
              <div>Private content</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProtectedRoute", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a session loading state", () => {
    mockedUseAuth.mockReturnValue({
      ...baseAuth,
      user: null,
      role: null,
      isAuthenticated: false,
      isLoading: true,
    });

    renderRoute();
    expect(screen.getByLabelText("Checking session")).toBeInTheDocument();
  });

  it("redirects unauthenticated users to login", () => {
    mockedUseAuth.mockReturnValue({
      ...baseAuth,
      user: null,
      role: null,
      isAuthenticated: false,
      isLoading: false,
    });

    renderRoute();
    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  it("renders content for an authenticated permitted user", () => {
    mockedUseAuth.mockReturnValue({
      ...baseAuth,
      user: {
        id: "user-1",
        email: "owner@example.com",
        firstName: "Practice",
        lastName: "Owner",
        role: "owner",
        practiceId: "practice-1",
        practiceName: "CoreDent",
        practiceCountry: "US",
      },
      role: "owner",
      isAuthenticated: true,
      isLoading: false,
    });

    renderRoute(["owner"]);
    expect(screen.getByText("Private content")).toBeInTheDocument();
  });

  it("blocks authenticated users without the required role", () => {
    mockedUseAuth.mockReturnValue({
      ...baseAuth,
      user: {
        id: "user-2",
        email: "desk@example.com",
        firstName: "Front",
        lastName: "Desk",
        role: "front_desk",
        practiceId: "practice-1",
        practiceName: "CoreDent",
        practiceCountry: "US",
      },
      role: "front_desk",
      isAuthenticated: true,
      isLoading: false,
    });

    renderRoute(["owner", "admin"]);
    expect(screen.getByRole("alert")).toHaveTextContent("Access denied");
    expect(screen.queryByText("Private content")).not.toBeInTheDocument();
  });
});