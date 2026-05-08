import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthContext } from "../auth-context";
import { useAuth } from "../auth-context";
import type { User, UserRole } from "@/types/api";

// Mock dependencies
vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

vi.mock("@/lib/analytics", () => ({
  analytics: { identify: vi.fn() },
  trackLogin: vi.fn(),
  trackLogout: vi.fn(),
}));

vi.mock("@/lib/csrf", () => ({
  refreshCsrfToken: vi.fn(),
  clearCsrfToken: vi.fn(),
}));

const mockUser: User = {
  id: "user-1",
  email: "test@example.com",
  firstName: "Test",
  lastName: "User",
  role: "admin",
  practiceId: "practice-1",
  practiceName: "Test Practice",
};

const TestComponent = () => {
  const { user, isAuthenticated, login, logout } = useAuth();

  return (
    <div>
      <div data-testid="auth-status">
        {isAuthenticated ? "Authenticated" : "Not Authenticated"}
      </div>
      {user && <div data-testid="user-name">{user.email}</div>}
      <button 
        data-testid="login-btn"
        onClick={() => login({ email: "test@example.com", password: "password" })}
      >
        Login
      </button>
      <button data-testid="logout-btn" onClick={logout}>Logout</button>
    </div>
  );
};

const createWrapper = (authValue?: {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  role: UserRole | null;
  login: (credentials: { email: string; password: string }) => Promise<boolean>;
  logout: () => Promise<void>;
  hasRole: (...roles: UserRole[]) => boolean;
}) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  const defaultAuthValue = {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    role: null,
    login: vi.fn().mockResolvedValue(true),
    logout: vi.fn().mockResolvedValue(undefined),
    hasRole: vi.fn().mockReturnValue(false),
  };

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={authValue || defaultAuthValue}>
        {children}
      </AuthContext.Provider>
    </QueryClientProvider>
  );
};

describe("AuthContext", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should provide auth context", () => {
    render(<TestComponent />, { wrapper: createWrapper() });

    expect(screen.getByTestId("auth-status")).toBeInTheDocument();
  });

  it("should show not authenticated initially", () => {
    render(<TestComponent />, { wrapper: createWrapper() });

    expect(screen.getByTestId("auth-status")).toHaveTextContent("Not Authenticated");
  });

  it("should handle login", async () => {
    const user = userEvent.setup();
    const mockLogin = vi.fn().mockResolvedValue(true);

    render(<TestComponent />, {
      wrapper: createWrapper({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        role: null,
        login: mockLogin,
        logout: vi.fn().mockResolvedValue(undefined),
        hasRole: vi.fn().mockReturnValue(false),
      }),
    });

    const loginButton = screen.getByTestId("login-btn");
    await user.click(loginButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled();
    });
  });

  it("should handle logout", async () => {
    const user = userEvent.setup();
    const mockLogout = vi.fn().mockResolvedValue(undefined);

    render(<TestComponent />, {
      wrapper: createWrapper({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        role: "admin",
        login: vi.fn().mockResolvedValue(true),
        logout: mockLogout,
        hasRole: vi.fn().mockReturnValue(true),
      }),
    });

    const logoutButton = screen.getByTestId("logout-btn");
    await user.click(logoutButton);

    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalled();
    });
  });
});
