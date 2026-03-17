import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/render';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import * as authContext from '@/contexts/auth-context';

// Mock the auth context
vi.mock('@/contexts/auth-context', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useAuth: vi.fn(),
  };
});

describe('ProtectedRoute', () => {
  it('renders children when user is authenticated', () => {
    vi.mocked(authContext.useAuth).mockReturnValue({
      user: {
        id: 'user-1',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'dentist',
        practiceId: 'practice-1',
        practiceName: 'Test Practice',
      },
      isAuthenticated: true,
      isLoading: false,
      role: 'dentist',
      login: vi.fn(),
      logout: vi.fn(),
      hasRole: vi.fn(() => true),
    });

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('shows loading state when authentication is loading', () => {
    vi.mocked(authContext.useAuth).mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      role: null,
      login: vi.fn(),
      logout: vi.fn(),
      hasRole: vi.fn(() => false),
    });

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('denies access when user lacks required role', () => {
    vi.mocked(authContext.useAuth).mockReturnValue({
      user: {
        id: 'user-1',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'front_desk',
        practiceId: 'practice-1',
        practiceName: 'Test Practice',
      },
      isAuthenticated: true,
      isLoading: false,
      role: 'front_desk',
      login: vi.fn(),
      logout: vi.fn(),
      hasRole: vi.fn(() => false),
    });

    render(
      <ProtectedRoute allowedRoles={['owner', 'admin']}>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });
});
