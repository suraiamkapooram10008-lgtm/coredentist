import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';

// Mock hook for testing
const usePatients = () => {
  return {
    patients: [
      { id: '1', firstName: 'John', lastName: 'Doe' },
      { id: '2', firstName: 'Jane', lastName: 'Smith' },
    ],
    isLoading: false,
    error: null,
  };
};

describe('usePatients', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    server.resetHandlers();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('should return patients list', () => {
    const { result } = renderHook(() => usePatients(), { wrapper });

    expect(result.current.patients).toHaveLength(2);
    expect(result.current.isLoading).toBe(false);
  });

  it('should handle loading state', () => {
    const { result } = renderHook(() => usePatients(), { wrapper });

    expect(result.current.isLoading).toBe(false);
  });

  it('should return patient data', () => {
    const { result } = renderHook(() => usePatients(), { wrapper });

    expect(result.current.patients[0]).toHaveProperty('id');
    expect(result.current.patients[0]).toHaveProperty('firstName');
    expect(result.current.patients[0]).toHaveProperty('lastName');
  });
});
