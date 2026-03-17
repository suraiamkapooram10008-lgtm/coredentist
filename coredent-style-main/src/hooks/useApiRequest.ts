import { useState, useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';
import type { ApiResponse } from '@/types/api';
import { logger } from '@/lib/logger';

interface UseApiRequestOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: any) => void;
  successMessage?: string;
  errorMessage?: string;
}

/**
 * Standard hook for managing API requests with loading, error, and toast notifications.
 */
export function useApiRequest<T>(
  apiFunc: (...args: any[]) => Promise<ApiResponse<T>>,
  options: UseApiRequestOptions<T> = {}
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const execute = useCallback(
    async (...args: any[]) => {
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await apiFunc(...args);
        
        if (response.success && response.data) {
          setData(response.data);
          if (options.successMessage) {
            toast({
              title: 'Success',
              description: options.successMessage,
            });
          }
          options.onSuccess?.(response.data);
          return response.data;
        } else {
          const message = response.error?.message || options.errorMessage || 'An error occurred';
          setError(message);
          toast({
            variant: 'destructive',
            title: 'Error',
            description: message,
          });
          options.onError?.(response.error);
          return null;
        }
      } catch (err) {
        const message = options.errorMessage || 'Network error occurred';
        setError(message);
        logger.error('API Request hook failed', err as Error);
        toast({
          variant: 'destructive',
          title: 'Error',
          description: message,
        });
        options.onError?.(err);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [apiFunc, options, toast]
  );

  return {
    data,
    setData,
    isLoading,
    error,
    execute,
  };
}
