import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider } from '../AuthContext';
import { useAuth } from '@/contexts/auth-context';
import { server } from '@/test/mocks/server';
import { http, HttpResponse } from 'msw';

// Mock the toast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

// Mock analytics
vi.mock('@/lib/analytics', () => ({
  analytics: {
    identify: vi.fn(),
  },
  trackLogin: vi.fn(),
  trackLogout: vi.fn(),
}));

// Mock CSRF functions
vi.mock('@/lib/csrf', () => ({
  refreshCsrfToken: vi.fn(),
  clearCsrfToken: vi.fn(),
}));

// Test component that uses auth context
const TestComponent = () => {
  const { user, isAuthenticated, login, logout, hasRole } = useAuth();

  return (
    <div>
      <div data-testid="auth-status">
        {isAuthenticated ? 'Authenticated' : 'Not authenticated'}
      </div>
      {user && (
        <div data-testid="user-info">
          {user.firstName} {user.lastName} - {user.role}
        </div>
      )}
      <button
        onClick={() => login({ email: 'test@example.com', password: 'password' })}
        data-testid="login-button"
      >
        Login
      </button>
      <button onClick={logout} data-testid="logout-button">
        Logout
      </button>
      <div data-testid="has-owner-role">
        {hasRole('owner') ? 'Has owner role' : 'No owner role'}
      </div>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock environment to disable dev bypass
    vi.stubEnv('MODE', 'test');
    vi.stubEnv('VITE_DEV_BYPASS_AUTH', 'false');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('should start with unauthenticated state', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('auth-status')).toHaveTextContent('Not authenticated');
    expect(screen.getByTestId('has-owner-role')).toHaveTextContent('No owner role');
  });

  it('should handle successful login', async () => {
    const user = userEvent.setup();
    
    // Mock successful login response
    server.use(
      http.post('/api/v1/auth/login', () => {
        return HttpResponse.json({
          access_token: 'mock-token',
          refresh_token: 'mock-refresh',
          token_type: 'bearer',
          expires_in: 900,
          csrf_token: 'mock-csrf',
        });
      }),
      http.get('/api/v1/auth/me', () => {
        return HttpResponse.json({
          id: 'user-1',
          email: 'test@example.com',
          firstName: 'Test',
          lastName: 'User',
          role: 'owner',
          practiceId: 'practice-1',
          practiceName: 'Test Practice',
        });
      })
    );

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await user.click(screen.getByTestId('login-button'));

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
    });

    expect(screen.getByTestId('user-info')).toHaveTextContent('Test User - owner');
    expect(screen.getByTestId('has-owner-role')).toHaveTextContent('Has owner role');
  });

  it('should handle login failure', async () => {
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
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await user.click(screen.getByTestId('login-button'));

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not authenticated');
    });
  });

  it('should handle logout', async () => {
    const user = userEvent.setup();
    
    // Mock successful login first
    server.use(
      http.post('/api/v1/auth/login', () => {
        return HttpResponse.json({
          access_token: 'mock-token',
          refresh_token: 'mock-refresh',
          token_type: 'bearer',
          expires_in: 900,
          csrf_token: 'mock-csrf',
        });
      }),
      http.get('/api/v1/auth/me', () => {
        return HttpResponse.json({
          id: 'user-1',
          email: 'test@example.com',
          firstName: 'Test',
          lastName: 'User',
          role: 'dentist',
          practiceId: 'practice-1',
          practiceName: 'Test Practice',
        });
      }),
      http.post('/api/v1/auth/logout', () => {
        return HttpResponse.json({ message: 'Successfully logged out' });
      })
    );

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Login first
    await user.click(screen.getByTestId('login-button'));
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
    });

    // Then logout
    await user.click(screen.getByTestId('logout-button'));
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not authenticated');
    });
  });

  it('should check user session on mount', async () => {
    // Mock existing session
    server.use(
      http.get('/api/v1/auth/me', () => {
        return HttpResponse.json({
          id: 'user-1',
          email: 'existing@example.com',
          firstName: 'Existing',
          lastName: 'User',
          role: 'dentist',
          practiceId: 'practice-1',
          practiceName: 'Test Practice',
        });
      })
    );

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
    });

    expect(screen.getByTestId('user-info')).toHaveTextContent('Existing User - dentist');
  });

  it('should handle role checking correctly', async () => {
    // Mock user with admin role
    server.use(
      http.get('/api/v1/auth/me', () => {
        return HttpResponse.json({
          id: 'user-1',
          email: 'admin@example.com',
          firstName: 'Admin',
          lastName: 'User',
          role: 'admin',
          practiceId: 'practice-1',
          practiceName: 'Test Practice',
        });
      })
    );

    const RoleTestComponent = () => {
      const { hasRole } = useAuth();
      return (
        <div>
          <div data-testid="has-admin">{hasRole('admin') ? 'Yes' : 'No'}</div>
          <div data-testid="has-owner">{hasRole('owner') ? 'Yes' : 'No'}</div>
          <div data-testid="has-multiple">{hasRole('admin', 'owner') ? 'Yes' : 'No'}</div>
        </div>
      );
    };

    render(
      <AuthProvider>
        <RoleTestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('has-admin')).toHaveTextContent('Yes');
    });

    expect(screen.getByTestId('has-owner')).toHaveTextContent('No');
    expect(screen.getByTestId('has-multiple')).toHaveTextContent('Yes');
  });

  it('should enable dev bypass in development mode', async () => {
    // Mock development mode with bypass enabled
    vi.stubEnv('MODE', 'development');
    vi.stubEnv('VITE_DEV_BYPASS_AUTH', 'true');

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
    });

    expect(screen.getByTestId('user-info')).toHaveTextContent('Dev User - owner');
  });
});