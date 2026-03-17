import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';
import { server } from '@/test/mocks/server';
import { http, HttpResponse } from 'msw';

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
const LoginForm = () => {
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const { login, isLoading } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
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

// Test wrapper with all providers
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          {children}
        </AuthProvider>
      </QueryClientProvider>
    </BrowserRouter>
  );
};

describe('Authentication Flow Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubEnv('MODE', 'test');
    vi.stubEnv('VITE_DEV_BYPASS_AUTH', 'false');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('should complete full login flow successfully', async () => {
    const user = userEvent.setup();

    // Mock successful API responses
    server.use(
      http.post('/api/v1/auth/login', async ({ request }) => {
        const body = await request.json() as any;
        expect(body.email).toBe('test@example.com');
        expect(body.password).toBe('password123');
        
        return HttpResponse.json({
          access_token: 'mock-access-token',
          refresh_token: 'mock-refresh-token',
          token_type: 'bearer',
          expires_in: 900,
          csrf_token: 'mock-csrf-token',
        });
      }),
      http.get('/api/v1/auth/me', () => {
        return HttpResponse.json({
          id: 'user-1',
          email: 'test@example.com',
          firstName: 'John',
          lastName: 'Doe',
          role: 'dentist',
          practiceId: 'practice-1',
          practiceName: 'Test Practice',
        });
      })
    );

    render(
      <TestWrapper>
        <TestApp />
      </TestWrapper>
    );

    // Should show login form initially
    expect(screen.getByTestId('login-form')).toBeInTheDocument();

    // Fill in login form
    await user.type(screen.getByTestId('email-input'), 'test@example.com');
    await user.type(screen.getByTestId('password-input'), 'password123');

    // Submit form
    await user.click(screen.getByTestId('login-button'));

    // Should show loading state
    expect(screen.getByText('Logging in...')).toBeInTheDocument();

    // Should show welcome message after successful login
    await waitFor(() => {
      expect(screen.getByTestId('welcome-message')).toHaveTextContent('Welcome, John Doe!');
    });

    expect(screen.getByTestId('user-role')).toHaveTextContent('Role: dentist');
    expect(screen.getByTestId('logout-button')).toBeInTheDocument();
  });

  it('should handle login failure gracefully', async () => {
    const user = userEvent.setup();

    // Mock failed login response
    server.use(
      http.post('/api/v1/auth/login', () => {
        return HttpResponse.json(
          { message: 'Invalid credentials' },
          { status: 401 }
        );
      })
    );

    render(
      <TestWrapper>
        <TestApp />
      </TestWrapper>
    );

    // Fill in login form with invalid credentials
    await user.type(screen.getByTestId('email-input'), 'test@example.com');
    await user.type(screen.getByTestId('password-input'), 'wrongpassword');
    await user.click(screen.getByTestId('login-button'));

    // Should remain on login form
    await waitFor(() => {
      expect(screen.getByTestId('login-form')).toBeInTheDocument();
    });

    // Should not show welcome message
    expect(screen.queryByTestId('welcome-message')).not.toBeInTheDocument();
  });

  it('should complete full logout flow', async () => {
    const user = userEvent.setup();

    // Mock successful login and logout
    server.use(
      http.post('/api/v1/auth/login', () => {
        return HttpResponse.json({
          access_token: 'mock-access-token',
          refresh_token: 'mock-refresh-token',
          token_type: 'bearer',
          expires_in: 900,
          csrf_token: 'mock-csrf-token',
        });
      }),
      http.get('/api/v1/auth/me', () => {
        return HttpResponse.json({
          id: 'user-1',
          email: 'test@example.com',
          firstName: 'Jane',
          lastName: 'Smith',
          role: 'admin',
          practiceId: 'practice-1',
          practiceName: 'Test Practice',
        });
      }),
      http.post('/api/v1/auth/logout', () => {
        return HttpResponse.json({ message: 'Successfully logged out' });
      })
    );

    render(
      <TestWrapper>
        <TestApp />
      </TestWrapper>
    );

    // Login first
    await user.type(screen.getByTestId('email-input'), 'test@example.com');
    await user.type(screen.getByTestId('password-input'), 'password123');
    await user.click(screen.getByTestId('login-button'));

    // Wait for login to complete
    await waitFor(() => {
      expect(screen.getByTestId('welcome-message')).toBeInTheDocument();
    });

    // Logout
    await user.click(screen.getByTestId('logout-button'));

    // Should return to login form
    await waitFor(() => {
      expect(screen.getByTestId('login-form')).toBeInTheDocument();
    });

    expect(screen.queryByTestId('welcome-message')).not.toBeInTheDocument();
  });

  it('should handle session restoration on app load', async () => {
    // Mock existing session
    server.use(
      http.get('/api/v1/auth/me', () => {
        return HttpResponse.json({
          id: 'user-1',
          email: 'existing@example.com',
          firstName: 'Existing',
          lastName: 'User',
          role: 'owner',
          practiceId: 'practice-1',
          practiceName: 'Test Practice',
        });
      })
    );

    render(
      <TestWrapper>
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
    const user = userEvent.setup();

    // Mock network error
    server.use(
      http.post('/api/v1/auth/login', () => {
        return HttpResponse.error();
      })
    );

    render(
      <TestWrapper>
        <TestApp />
      </TestWrapper>
    );

    await user.type(screen.getByTestId('email-input'), 'test@example.com');
    await user.type(screen.getByTestId('password-input'), 'password123');
    await user.click(screen.getByTestId('login-button'));

    // Should remain on login form after network error
    await waitFor(() => {
      expect(screen.getByTestId('login-form')).toBeInTheDocument();
    });
  });

  it('should handle token refresh failure', async () => {
    const user = userEvent.setup();

    // Mock successful login but failed user fetch (simulating token expiry)
    server.use(
      http.post('/api/v1/auth/login', () => {
        return HttpResponse.json({
          access_token: 'mock-access-token',
          refresh_token: 'mock-refresh-token',
          token_type: 'bearer',
          expires_in: 900,
          csrf_token: 'mock-csrf-token',
        });
      }),
      http.get('/api/v1/auth/me', () => {
        return HttpResponse.json(
          { message: 'Token expired' },
          { status: 401 }
        );
      })
    );

    render(
      <TestWrapper>
        <TestApp />
      </TestWrapper>
    );

    await user.type(screen.getByTestId('email-input'), 'test@example.com');
    await user.type(screen.getByTestId('password-input'), 'password123');
    await user.click(screen.getByTestId('login-button'));

    // Should remain on login form if user fetch fails
    await waitFor(() => {
      expect(screen.getByTestId('login-form')).toBeInTheDocument();
    });
  });
});