import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';
import { useAuth } from '@/contexts/auth-context';
import { server } from '@/test/mocks/server';
import { http, HttpResponse } from 'msw';

// Mock dependencies
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

vi.mock('@/lib/analytics', () => ({
  analytics: { identify: vi.fn() },
  trackLogin: vi.fn(),
  trackLogout: vi.fn(),
}));

vi.mock('@/lib/csrf', () => ({
  refreshCsrfToken: vi.fn(),
  clearCsrfToken: vi.fn(),
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        {children}
      </AuthProvider>
    </QueryClientProvider>
  );
};

describe('useAuth hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubEnv('MODE', 'test');
    vi.stubEnv('VITE_DEV_BYPASS_AUTH', 'false');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('should return initial unauthenticated state', async () => {
    server.use(
      http.get('/api/v1/auth/me', () => {
        return HttpResponse.json(
          { message: 'Unauthorized' },
          { status: 401 }
        );
      })
    );

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.role).toBeNull();
  });

  it('should authenticate user successfully', async () => {
    const mockUser = {
      id: 'user-1',
      email: 'test@example.com',
      firstName: 'Test',
      lastName: 'User',
      role: 'dentist',
      practiceId: 'practice-1',
      practiceName: 'Test Practice',
    };

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
        return HttpResponse.json(mockUser);
      })
    );

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Perform login
    const loginResult = await result.current.login({
      email: 'test@example.com',
      password: 'password123',
    });

    expect(loginResult).toBe(true);

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.role).toBe('dentist');
    });
  });

  it('should handle login failure', async () => {
    server.use(
      http.post('/api/v1/auth/login', () => {
        return HttpResponse.json(
          { message: 'Invalid credentials' },
          { status: 401 }
        );
      })
    );

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const loginResult = await result.current.login({
      email: 'test@example.com',
      password: 'wrongpassword',
    });

    expect(loginResult).toBe(false);
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('should logout user successfully', async () => {
    const mockUser = {
      id: 'user-1',
      email: 'test@example.com',
      firstName: 'Test',
      lastName: 'User',
      role: 'admin',
      practiceId: 'practice-1',
      practiceName: 'Test Practice',
    };

    server.use(
      http.get('/api/v1/auth/me', () => {
        return HttpResponse.json(mockUser);
      }),
      http.post('/api/v1/auth/logout', () => {
        return HttpResponse.json({ message: 'Successfully logged out' });
      })
    );

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    // Wait for initial session check
    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    // Perform logout
    await result.current.logout();

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.role).toBeNull();
    });
  });

  it('should check user roles correctly', async () => {
    const mockUser = {
      id: 'user-1',
      email: 'admin@example.com',
      firstName: 'Admin',
      lastName: 'User',
      role: 'admin',
      practiceId: 'practice-1',
      practiceName: 'Test Practice',
    };

    server.use(
      http.get('/api/v1/auth/me', () => {
        return HttpResponse.json(mockUser);
      })
    );

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    // Test role checking
    expect(result.current.hasRole('admin')).toBe(true);
    expect(result.current.hasRole('owner')).toBe(false);
    expect(result.current.hasRole('dentist')).toBe(false);
    expect(result.current.hasRole('admin', 'owner')).toBe(true);
    expect(result.current.hasRole('dentist', 'hygienist')).toBe(false);
  });

  it('should handle network errors during login', async () => {
    server.use(
      http.post('/api/v1/auth/login', () => {
        return HttpResponse.error();
      })
    );

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const loginResult = await result.current.login({
      email: 'test@example.com',
      password: 'password123',
    });

    expect(loginResult).toBe(false);
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('should restore session on mount', async () => {
    const mockUser = {
      id: 'user-1',
      email: 'existing@example.com',
      firstName: 'Existing',
      lastName: 'User',
      role: 'owner',
      practiceId: 'practice-1',
      practiceName: 'Test Practice',
    };

    server.use(
      http.get('/api/v1/auth/me', () => {
        return HttpResponse.json(mockUser);
      })
    );

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    // Should start loading
    expect(result.current.isLoading).toBe(true);

    // Should restore session
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
    });
  });

  it('should handle failed session restoration', async () => {
    server.use(
      http.get('/api/v1/auth/me', () => {
        return HttpResponse.json(
          { message: 'Session expired' },
          { status: 401 }
        );
      })
    );

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('should enable dev bypass in development mode', async () => {
    vi.stubEnv('MODE', 'development');
    vi.stubEnv('VITE_DEV_BYPASS_AUTH', 'true');

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.email).toBe('dev@coredent.com');
    expect(result.current.user?.role).toBe('owner');
  });

  it('should handle logout even when API fails', async () => {
    const mockUser = {
      id: 'user-1',
      email: 'test@example.com',
      firstName: 'Test',
      lastName: 'User',
      role: 'dentist',
      practiceId: 'practice-1',
      practiceName: 'Test Practice',
    };

    server.use(
      http.get('/api/v1/auth/me', () => {
        return HttpResponse.json(mockUser);
      }),
      http.post('/api/v1/auth/logout', () => {
        return HttpResponse.error();
      })
    );

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    // Logout should still work even if API fails
    await result.current.logout();

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });
  });
});