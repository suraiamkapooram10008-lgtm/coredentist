import { useState, useCallback, useEffect } from 'react';
import { logger } from '@/lib/logger';

interface UseApiResult<T> {
  loading: boolean;
  data: T | null;
  error: Error | null;
  refetch: () => void;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export function useApi<T = unknown>(endpoint: string): UseApiResult<T> {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [fetchTrigger, setFetchTrigger] = useState(0);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = (await response.json()) as T;
      setData(result);
    } catch (err) {
      const fetchError = err instanceof Error ? err : new Error(String(err));
      setError(fetchError);
      logger.error(`useApi fetch failed: ${endpoint}`, fetchError);
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  useEffect(() => {
    fetchData();
  }, [fetchData, fetchTrigger]);

  const refetch = useCallback(() => {
    setFetchTrigger((prev) => prev + 1);
  }, []);

  return { loading, data, error, refetch };
}
