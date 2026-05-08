/**
 * Generic CRUD Hook
 * Eliminates duplication across 19+ CRUD hooks
 * Provides standardized data fetching, mutation, and state management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';
import type { CrudService, ListParams } from '@/lib/apiServiceFactory';
import type { PaginatedResponse } from '@/types/common';
import type { AsyncCallback } from '@/types/utils';

// ============================================
// Query Key Factory
// ============================================

/**
 * Create standardized query keys for a resource
 */
export function createQueryKeys(resource: string) {
  return {
    all: [resource] as const,
    lists: () => [...createQueryKeys(resource).all, 'list'] as const,
    list: (params?: ListParams) => [...createQueryKeys(resource).lists(), params] as const,
    details: () => [...createQueryKeys(resource).all, 'detail'] as const,
    detail: (id: string) => [...createQueryKeys(resource).details(), id] as const,
  };
}

/**
 * Resolve resource name from service or options.
 * Prevents cache key collisions between different resource types.
 */
function resolveResourceName(
   
  service: any,
  resourceName?: string
): string {
  return resourceName || service?.resource || 'unknown';
}

// ============================================
// Generic List Hook
// ============================================

/**
 * Generic hook for fetching paginated lists
 * Replaces 15+ similar list hooks
 *
 * @example
 * const { data, isLoading, error } = useList(userApi, { page: 1, limit: 10 }, { resourceName: 'users' });
 */
export function useList<T extends { id: string }>(
  service: CrudService<T> | { list: (params?: ListParams) => Promise<PaginatedResponse<T>> },
  params?: ListParams,
  options?: {
    enabled?: boolean;
    staleTime?: number;
    cacheTime?: number;
    resourceName?: string;  // Required: unique per service to prevent cache collisions
  }
) {
  const resource = resolveResourceName(service, options?.resourceName);
  const queryKeys = createQueryKeys(resource);

  return useQuery({
    queryKey: queryKeys.list(params),
    queryFn: () => service.list(params),
    enabled: options?.enabled !== false,
    staleTime: options?.staleTime ?? 5 * 60 * 1000, // 5 minutes
    gcTime: options?.cacheTime ?? 10 * 60 * 1000, // 10 minutes
  });
}

// ============================================
// Generic Get Hook
// ============================================

/**
 * Generic hook for fetching single item
 * Replaces 10+ similar get hooks
 *
 * @example
 * const { data, isLoading, error } = useGet(userApi, 'user-123', { resourceName: 'users' });
 */
export function useGet<T extends { id: string }>(
  service: CrudService<T> | { get: (id: string) => Promise<T | null> },
  id: string | null | undefined,
  options?: {
    enabled?: boolean;
    staleTime?: number;
    cacheTime?: number;
    resourceName?: string;  // Required: unique per service to prevent cache collisions
  }
) {
  const resource = resolveResourceName(service, options?.resourceName);
  const queryKeys = createQueryKeys(resource);

  return useQuery({
    queryKey: queryKeys.detail(id || ''),
    queryFn: () => (id ? service.get(id) : Promise.resolve(null)),
    enabled: (options?.enabled !== false) && !!id,
    staleTime: options?.staleTime ?? 5 * 60 * 1000,
    gcTime: options?.cacheTime ?? 10 * 60 * 1000,
  });
}

// ============================================
// Generic Create Hook
// ============================================

/**
 * Generic hook for creating items
 * Replaces 8+ similar create hooks
 *
 * @example
 * const { mutate, isLoading } = useCreate(userApi, {
 *   resourceName: 'users',
 *   onSuccess: () => toast({ title: 'User created' })
 * });
 * mutate({ name: 'John' });
 */
export function useCreate<T extends { id: string }, CreateData = Partial<T>>(
  service: CrudService<T, CreateData> | { create: (data: CreateData) => Promise<T> },
  options?: {
    onSuccess?: AsyncCallback<T>;
    onError?: AsyncCallback<Error>;
    successMessage?: string;
    errorMessage?: string;
    resourceName?: string;  // Required: unique per service to prevent cache collisions
  }
) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const resource = resolveResourceName(service, options?.resourceName);
  const queryKeys = createQueryKeys(resource);

  return useMutation({
    mutationFn: (data: CreateData) => service.create(data),
    onSuccess: async (data) => {
      // Invalidate list queries for this resource
      await queryClient.invalidateQueries({ queryKey: queryKeys.lists() });

      if (options?.successMessage) {
        toast({ title: options.successMessage });
      }

      if (options?.onSuccess) {
        await options.onSuccess(data);
      }
    },
    onError: async (error: Error) => {
      if (options?.errorMessage) {
        toast({
          title: options.errorMessage,
          description: error.message,
          variant: 'destructive',
        });
      }

      if (options?.onError) {
        await options.onError(error);
      }
    },
  });
}

// ============================================
// Generic Update Hook
// ============================================

/**
 * Generic hook for updating items
 * Replaces 8+ similar update hooks
 *
 * @example
 * const { mutate, isLoading } = useUpdate(userApi, {
 *   resourceName: 'users',
 *   onSuccess: () => toast({ title: 'User updated' })
 * });
 * mutate({ id: 'user-123', data: { name: 'Jane' } });
 */
export function useUpdate<T extends { id: string }, UpdateData = Partial<T>>(
  service: CrudService<T, unknown, UpdateData> | { update: (id: string, data: UpdateData) => Promise<T | null> },
  options?: {
    onSuccess?: AsyncCallback<T | null>;
    onError?: AsyncCallback<Error>;
    successMessage?: string;
    errorMessage?: string;
    resourceName?: string;  // Required: unique per service to prevent cache collisions
  }
) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const resource = resolveResourceName(service, options?.resourceName);
  const queryKeys = createQueryKeys(resource);

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateData }) => service.update(id, data),
    onSuccess: async (data, { id }) => {
      // Invalidate both list and detail queries for this resource
      await queryClient.invalidateQueries({ queryKey: queryKeys.lists() });
      await queryClient.invalidateQueries({ queryKey: queryKeys.detail(id) });

      if (options?.successMessage) {
        toast({ title: options.successMessage });
      }

      if (options?.onSuccess) {
        await options.onSuccess(data);
      }
    },
    onError: async (error: Error) => {
      if (options?.errorMessage) {
        toast({
          title: options.errorMessage,
          description: error.message,
          variant: 'destructive',
        });
      }

      if (options?.onError) {
        await options.onError(error);
      }
    },
  });
}

// ============================================
// Generic Delete Hook
// ============================================

/**
 * Generic hook for deleting items
 * Replaces 8+ similar delete hooks
 *
 * @example
 * const { mutate, isLoading } = useDelete(userApi, {
 *   resourceName: 'users',
 *   onSuccess: () => toast({ title: 'User deleted' })
 * });
 * mutate('user-123');
 */
export function useDelete<T extends { id: string }>(
  service: CrudService<T> | { delete: (id: string) => Promise<void> },
  options?: {
    onSuccess?: AsyncCallback<void>;
    onError?: AsyncCallback<Error>;
    successMessage?: string;
    errorMessage?: string;
    resourceName?: string;  // Required: unique per service to prevent cache collisions
  }
) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const resource = resolveResourceName(service, options?.resourceName);
  const queryKeys = createQueryKeys(resource);

  return useMutation({
    mutationFn: (id: string) => service.delete(id),
    onSuccess: async () => {
      // Invalidate list queries for this resource
      await queryClient.invalidateQueries({ queryKey: queryKeys.lists() });

      if (options?.successMessage) {
        toast({ title: options.successMessage });
      }

      if (options?.onSuccess) {
        await options.onSuccess();
      }
    },
    onError: async (error: Error) => {
      if (options?.errorMessage) {
        toast({
          title: options.errorMessage,
          description: error.message,
          variant: 'destructive',
        });
      }

      if (options?.onError) {
        await options.onError(error);
      }
    },
  });
}

// ============================================
// Combined CRUD Hook
// ============================================

/**
 * Combined hook for all CRUD operations
 * Useful when you need multiple operations on the same resource
 *
 * @example
 * const crud = useCrud(userApi, 'users');
 * const { data: users } = crud.useList({ page: 1 });
 * const { mutate: create } = crud.useCreate();
 * const { mutate: update } = crud.useUpdate();
 * const { mutate: remove } = crud.useDelete();
 */
export function useCrud<T extends { id: string }, CreateData = Partial<T>, UpdateData = Partial<T>>(
  service: CrudService<T, CreateData, UpdateData>,
  resourceName?: string
) {
  const resolvedName = resolveResourceName(service, resourceName);
  return {
    useList: (params?: ListParams, options?: Parameters<typeof useList>[2]) =>
      useList(service, params, { ...options, resourceName: resolvedName }),
    useGet: (id: string | null | undefined, options?: Parameters<typeof useGet>[2]) =>
      useGet(service, id, { ...options, resourceName: resolvedName }),
    useCreate: (options?: Parameters<typeof useCreate>[1]) =>
      useCreate(service, { ...options, resourceName: resolvedName }),
    useUpdate: (options?: Parameters<typeof useUpdate>[1]) =>
      useUpdate(service, { ...options, resourceName: resolvedName }),
    useDelete: (options?: Parameters<typeof useDelete>[1]) =>
      useDelete(service, { ...options, resourceName: resolvedName }),
  };
}
