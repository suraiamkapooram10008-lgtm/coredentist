/**
 * useDashboardMetrics Hook
 * Fetches and manages dashboard metrics data
 */

import { useQuery } from '@tanstack/react-query';
import { reportsApi } from '@/services/reportsApi';
import type { DashboardMetrics } from '@/types/reports';

interface UseDashboardMetricsOptions {
  from?: Date;
  to?: Date;
  enabled?: boolean;
}

interface UseDashboardMetricsResult {
  metrics: DashboardMetrics | null;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}

/**
 * Hook to fetch dashboard metrics
 * 
 * @param options - Configuration options
 * @returns Dashboard metrics data and loading state
 * 
 * @example
 * const { metrics, isLoading } = useDashboardMetrics({
 *   from: startOfMonth,
 *   to: today
 * });
 */
export function useDashboardMetrics(
  options: UseDashboardMetricsOptions = {}
): UseDashboardMetricsResult {
  const { from, to, enabled = true } = options;

  const { data: response, isLoading, isError, error } = useQuery({
    queryKey: ['dashboard', 'metrics', from?.toISOString(), to?.toISOString()],
    queryFn: () => reportsApi.getDashboardMetrics({ from, to }),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled,
  });

  const metrics = response?.success && response.data ? response.data : null;

  return {
    metrics,
    isLoading,
    isError,
    error: error instanceof Error ? error : null,
  };
}
