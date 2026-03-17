import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { AuthContext } from '@/contexts/auth-context';
import type { User, UserRole } from '@/types/api';

// Create a custom render function that includes providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  user?: User | null;
  isAuthenticated?: boolean;
  isLoading?: boolean;
}

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

export function renderWithProviders(
  ui: ReactElement,
  {
    user = null,
    isAuthenticated = false,
    isLoading = false,
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  const testQueryClient = createTestQueryClient();

  const mockAuthValue = {
    user,
    isAuthenticated,
    isLoading,
    role: user?.role || null,
    login: vi.fn(),
    logout: vi.fn(),
    hasRole: vi.fn((...roles: UserRole[]) => {
      if (!user) return false;
      return roles.includes(user.role);
    }),
  };

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={testQueryClient}>
        <AuthContext.Provider value={mockAuthValue}>
          <BrowserRouter>{children}</BrowserRouter>
        </AuthContext.Provider>
      </QueryClientProvider>
    );
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    user,
    mockAuthValue,
  };
}

// Re-export everything from testing library
export * from '@testing-library/react';
export { renderWithProviders as render };

// Mock user factory
export function createMockUser(overrides?: Partial<User>): User {
  return {
    id: 'test-user-id',
    email: 'test@example.com',
    firstName: 'Test',
    lastName: 'User',
    role: 'dentist',
    practiceId: 'test-practice-id',
    practiceName: 'Test Practice',
    ...overrides,
  };
}
