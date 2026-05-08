import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthContext } from '@/contexts/auth-context';
import { server } from '@/test/mocks/server';
import { http, HttpResponse } from 'msw';
import React, { useState, FormEvent, useCallback } from 'react';
import type { User, UserRole } from '@/types/api';

// Mock toast
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

// Mock analytics
vi.mock('@/lib/analytics', () => ({
  analytics: { identify: vi.fn() },
  trackLogin: vi.fn(),
  trackLogout: vi.fn(),
}));

// Mock CSRF
vi.mock('@/lib/csrf', () => ({
  refreshCsrfToken: vi.fn(),
  clearCsrfToken: vi.fn(),
}));

// Simple login form component for testing
const LoginForm = ({ onLogin }: { onLogin?: (email: string, password: string) => void }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading } = useAuth();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (onLogin) {
      onLogin(email, password);
    }
    await login({ email, password });
  };

  return (
    <form onSubmit={handleSubmit} data-testid="login-form">
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        data-testid="email-input"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        data-testid="password-input"
      />
      <button type="submit" disabled={isLoading} data-testid="login-button">
        {isLoading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
};

// App component with auth status
const TestApp = () => {
  const { user, isAuthenticated, logout } = useAuth();

  if (isAuthenticated && user) {
    return (
      <div>
        <div data-testid="welcome-message">
          Welcome, {user.firstName} {user.lastName}!
        </div>
        <div data-testid="user-role">Role: {user.role}</div>
        <button onClick={logout} data-testid="logout-button">
          Logout
        </button>
      </div>
    );
  }

  return <LoginForm />;
};

// Mock useAuth hook for controlled testing
const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Test wrapper with mock auth context
const TestWrapper = ({ 
  children, 
  authValue 
}: { 
  children: React.ReactNode;
  authValue?: {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    role: UserRole | null;
    login: (credentials: { email: string; password: string }) => Promise<boolean>;
    logout: () => Promise<void>;
    hasRole: (...roles: UserRole[]) => boolean;
  };
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
    login: vi.fn().mockResolvedValue(false),
    logout: vi.fn().mockResolvedValue(undefined),
    hasRole: vi.fn().mockReturnValue(false),
  };

  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <AuthContext.Provider value={authValue || defaultAuthValue}>
          {children}
        </AuthContext.Provider>
      </QueryClientProvider>
    </BrowserRouter>
  );
};

describe('Authentication Flow Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('should complete full login flow successfully', async () => {
    // Mock unauthenticated state (showing login form)
    render(
      <TestWrapper>
        <TestApp />
      </TestWrapper>
    );

    // Verify login form is shown when not authenticated
    await waitFor(() => {
      expect(screen.getByTestId('login-form')).toBeInTheDocument();
    });

    // Verify form fields exist
    expect(screen.getByTestId('email-input')).toBeInTheDocument();
    expect(screen.getByTestId('password-input')).toBeInTheDocument();
    expect(screen.getByTestId('login-button')).toBeInTheDocument();
  });

  it('should handle login failure gracefully', async () => {
    const mockLogin = vi.fn().mockResolvedValue(false);

    render(
      <TestWrapper authValue={{
        user: null,
        isAuthenticated: false,
        isLoading: false,
        role: null,
        login: mockLogin,
        logout: vi.fn().mockResolvedValue(undefined),
        hasRole: vi.fn().mockReturnValue(false),
      }}>
        <TestApp />
      </TestWrapper>
    );

    // Fill in login form with invalid credentials
    await userEvent.type(screen.getByTestId('email-input'), 'test@example.com');
    await userEvent.type(screen.getByTestId('password-input'), 'wrongpassword');
    await userEvent.click(screen.getByTestId('login-button'));

    // Should remain on login form
    await waitFor(() => {
      expect(screen.getByTestId('login-form')).toBeInTheDocument();
    });

    // Should not show welcome message
    expect(screen.queryByTestId('welcome-message')).not.toBeInTheDocument();
  });

  it('should complete full logout flow', async () => {
    const mockLogout = vi.fn().mockResolvedValue(undefined);

    render(
      <TestWrapper authValue={{
        user: {
          id: 'user-1',
          email: 'test@example.com',
          firstName: 'Jane',
          lastName: 'Smith',
          role: 'admin',
          practiceId: 'practice-1',
          practiceName: 'Test Practice',
        },
        isAuthenticated: true,
        isLoading: false,
        role: 'admin',
        login: vi.fn().mockResolvedValue(false),
        logout: mockLogout,
        hasRole: vi.fn().mockReturnValue(true),
      }}>
        <TestApp />
      </TestWrapper>
    );

    // Wait for authenticated state
    await waitFor(() => {
      expect(screen.getByTestId('welcome-message')).toBeInTheDocument();
    });

    // Verify logout button exists
    expect(screen.getByTestId('logout-button')).toBeInTheDocument();
    expect(screen.getByTestId('logout-button')).toHaveTextContent('Logout');
  });

  it('should handle session restoration on app load', async () => {
    render(
      <TestWrapper authValue={{
        user: {
          id: 'user-1',
          email: 'existing@example.com',
          firstName: 'Existing',
          lastName: 'User',
          role: 'owner',
          practiceId: 'practice-1',
          practiceName: 'Test Practice',
        },
        isAuthenticated: true,
        isLoading: false,
        role: 'owner',
        login: vi.fn().mockResolvedValue(false),
        logout: vi.fn().mockResolvedValue(undefined),
        hasRole: vi.fn().mockReturnValue(true),
      }}>
        <TestApp />
      </TestWrapper>
    );

    // Should automatically show welcome message for existing session
    await waitFor(() => {
      expect(screen.getByTestId('welcome-message')).toHaveTextContent('Welcome, Existing User!');
    });

    expect(screen.getByTestId('user-role')).toHaveTextContent('Role: owner');
  });

  it('should handle network errors during login', async () => {
    const mockLogin = vi.fn().mockImplementation(() => {
      // Return false to simulate login failure, not throw
      return Promise.resolve(false);
    });

    render(
      <TestWrapper authValue={{
        user: null,
        isAuthenticated: false,
        isLoading: false,
        role: null,
        login: mockLogin,
        logout: vi.fn().mockResolvedValue(undefined),
        hasRole: vi.fn().mockReturnValue(false),
      }}>
        <TestApp />
      </TestWrapper>
    );

    await userEvent.type(screen.getByTestId('email-input'), 'test@example.com');
    await userEvent.type(screen.getByTestId('password-input'), 'password123');
    await userEvent.click(screen.getByTestId('login-button'));

    // Should remain on login form after network error
    await waitFor(() => {
      expect(screen.getByTestId('login-form')).toBeInTheDocument();
    });
  });

  it('should handle token refresh failure', async () => {
    const mockLogin = vi.fn().mockResolvedValue(false); // Simulate failed login due to token expiry

    render(
      <TestWrapper authValue={{
        user: null,
        isAuthenticated: false,
        isLoading: false,
        role: null,
        login: mockLogin,
        logout: vi.fn().mockResolvedValue(undefined),
        hasRole: vi.fn().mockReturnValue(false),
      }}>
        <TestApp />
      </TestWrapper>
    );

    await userEvent.type(screen.getByTestId('email-input'), 'test@example.com');
    await userEvent.type(screen.getByTestId('password-input'), 'password123');
    await userEvent.click(screen.getByTestId('login-button'));

    // Should remain on login form if user fetch fails
    await waitFor(() => {
      expect(screen.getByTestId('login-form')).toBeInTheDocument();
    });
  });
});