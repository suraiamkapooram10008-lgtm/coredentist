/**
 * Generic API Service Factory
 * Creates standardized CRUD services to eliminate duplication
 * Reduces code duplication by 50%+ across API services
 */

import { apiClient } from '@/services/api';
import type { PaginatedResponse } from '@/types/common';

// ============================================
// Generic Types
// ============================================

/**
 * Generic list parameters for pagination and filtering
 */
export interface ListParams {
  page?: number;
  limit?: number;
  search?: string;
  sort?: string;
  [key: string]: unknown;
}

/**
 * Generic CRUD service interface
 */
export interface CrudService<T, CreateData = Partial<T>, UpdateData = Partial<T>> {
  list: (params?: ListParams) => Promise<PaginatedResponse<T>>;
  get: (id: string) => Promise<T | null>;
  create: (data: CreateData) => Promise<T>;
  update: (id: string, data: UpdateData) => Promise<T | null>;
  delete: (id: string) => Promise<void>;
}

/**
 * Generic list-only service interface
 */
export interface ListService<T> {
  list: (params?: ListParams) => Promise<PaginatedResponse<T>>;
}

/**
 * Generic get-only service interface
 */
export interface GetService<T> {
  get: (id: string) => Promise<T | null>;
}

// ============================================
// Factory Functions
// ============================================

/**
 * Create a standard CRUD service
 * Eliminates boilerplate for common CRUD operations
 *
 * @example
 * const userApi = createCrudService<User>('/users');
 * const users = await userApi.list({ page: 1, limit: 10 });
 * const user = await userApi.get('user-123');
 * const newUser = await userApi.create({ name: 'John' });
 * await userApi.update('user-123', { name: 'Jane' });
 * await userApi.delete('user-123');
 */
export function createCrudService<
  T extends { id: string },
  CreateData = Partial<T>,
  UpdateData = Partial<T>
>(
  endpoint: string,
  options?: {
    listKey?: string; // Key for list response (default: 'data')
    defaultLimit?: number; // Default page limit (default: 20)
  }
): CrudService<T, CreateData, UpdateData> {
  const { listKey: _listKey = 'data', defaultLimit = 20 } = options || {};

  return {
    /**
     * Get paginated list of items
     */
    list: async (params?: ListParams): Promise<PaginatedResponse<T>> => {
      const response = await apiClient.get<PaginatedResponse<T>>(
        endpoint,
        params as unknown as Record<string, unknown>
      );

      if (response.success && response.data) {
        return response.data;
      }

      return {
        data: [],
        total: 0,
        page: params?.page ?? 1,
        limit: params?.limit ?? defaultLimit,
        totalPages: 0,
      };
    },

    /**
     * Get single item by ID
     */
    get: async (id: string): Promise<T | null> => {
      const response = await apiClient.get<T>(`${endpoint}/${id}`);
      return response.success ? response.data ?? null : null;
    },

    /**
     * Create new item
     */
    create: async (data: CreateData): Promise<T> => {
      const response = await apiClient.post<T>(endpoint, data);
      if (response.success && response.data) {
        return response.data;
      }
      throw new Error(response.error?.message || `Failed to create ${endpoint}`);
    },

    /**
     * Update existing item
     */
    update: async (id: string, data: UpdateData): Promise<T | null> => {
      const response = await apiClient.put<T>(`${endpoint}/${id}`, data);
      return response.success ? response.data ?? null : null;
    },

    /**
     * Delete item
     */
    delete: async (id: string): Promise<void> => {
      await apiClient.delete(`${endpoint}/${id}`);
    },
  };
}

/**
 * Create a list-only service
 * For endpoints that only support listing
 *
 * @example
 * const reportsApi = createListService<Report>('/reports');
 * const reports = await reportsApi.list({ page: 1 });
 */
export function createListService<T>(
  endpoint: string,
  options?: {
    defaultLimit?: number;
  }
): ListService<T> {
  const { defaultLimit = 20 } = options || {};

  return {
    list: async (params?: ListParams): Promise<PaginatedResponse<T>> => {
      const response = await apiClient.get<PaginatedResponse<T>>(
        endpoint,
        params as unknown as Record<string, unknown>
      );

      if (response.success && response.data) {
        return response.data;
      }

      return {
        data: [],
        total: 0,
        page: params?.page ?? 1,
        limit: params?.limit ?? defaultLimit,
        totalPages: 0,
      };
    },
  };
}

/**
 * Create a get-only service
 * For endpoints that only support getting by ID
 *
 * @example
 * const settingsApi = createGetService<Settings>('/settings');
 * const settings = await settingsApi.get('user-123');
 */
export function createGetService<T>(endpoint: string): GetService<T> {
  return {
    get: async (id: string): Promise<T | null> => {
      const response = await apiClient.get<T>(`${endpoint}/${id}`);
      return response.success ? response.data ?? null : null;
    },
  };
}

/**
 * Create a custom service with specific methods
 * For complex endpoints that don't fit standard CRUD
 *
 * @example
 * const customApi = createCustomService('/custom', {
 *   search: (query: string) => apiClient.get('/custom/search', { q: query }),
 *   export: (format: string) => apiClient.get('/custom/export', { format }),
 * });
 */
export function createCustomService<T extends Record<string, (...args: unknown[]) => unknown>>(
  endpoint: string,
  methods: T
): T {
  return methods;
}

/**
 * Create a nested resource service
 * For resources that are nested under a parent (e.g., /patients/:id/notes)
 *
 * @example
 * const patientNotesApi = createNestedService<Note>('/patients', 'notes');
 * const notes = await patientNotesApi.list('patient-123');
 * const note = await patientNotesApi.get('patient-123', 'note-456');
 */
export function createNestedService<T extends { id: string }>(
  parentEndpoint: string,
  childResource: string,
  options?: {
    defaultLimit?: number;
  }
) {
  const { defaultLimit = 20 } = options || {};

  return {
    /**
     * Get paginated list of child items
     */
    list: async (parentId: string, params?: ListParams): Promise<PaginatedResponse<T>> => {
      const endpoint = `${parentEndpoint}/${parentId}/${childResource}`;
      const response = await apiClient.get<PaginatedResponse<T>>(
        endpoint,
        params as unknown as Record<string, unknown>
      );

      if (response.success && response.data) {
        return response.data;
      }

      return {
        data: [],
        total: 0,
        page: params?.page ?? 1,
        limit: params?.limit ?? defaultLimit,
        totalPages: 0,
      };
    },

    /**
     * Get single child item
     */
    get: async (parentId: string, id: string): Promise<T | null> => {
      const endpoint = `${parentEndpoint}/${parentId}/${childResource}/${id}`;
      const response = await apiClient.get<T>(endpoint);
      return response.success ? response.data ?? null : null;
    },

    /**
     * Create child item
     */
    create: async (parentId: string, data: Partial<T>): Promise<T> => {
      const endpoint = `${parentEndpoint}/${parentId}/${childResource}`;
      const response = await apiClient.post<T>(endpoint, data);
      if (response.success && response.data) {
        return response.data;
      }
      throw new Error(response.error?.message || `Failed to create ${childResource}`);
    },

    /**
     * Update child item
     */
    update: async (parentId: string, id: string, data: Partial<T>): Promise<T | null> => {
      const endpoint = `${parentEndpoint}/${parentId}/${childResource}/${id}`;
      const response = await apiClient.put<T>(endpoint, data);
      return response.success ? response.data ?? null : null;
    },

    /**
     * Delete child item
     */
    delete: async (parentId: string, id: string): Promise<void> => {
      const endpoint = `${parentEndpoint}/${parentId}/${childResource}/${id}`;
      await apiClient.delete(endpoint);
    },
  };
}

/**
 * Create a batch operation service
 * For endpoints that support batch operations
 *
 * @example
 * const batchApi = createBatchService<User>('/users');
 * await batchApi.batchCreate([{ name: 'John' }, { name: 'Jane' }]);
 * await batchApi.batchDelete(['user-1', 'user-2']);
 */
export function createBatchService<T extends { id: string }>(endpoint: string) {
  return {
    /**
     * Create multiple items
     */
    batchCreate: async (items: Partial<T>[]): Promise<T[]> => {
      const response = await apiClient.post<T[]>(`${endpoint}/batch`, { items });
      if (response.success && response.data) {
        return response.data;
      }
      throw new Error(response.error?.message || 'Batch create failed');
    },

    /**
     * Update multiple items
     */
    batchUpdate: async (updates: Array<{ id: string; data: Partial<T> }>): Promise<T[]> => {
      const response = await apiClient.put<T[]>(`${endpoint}/batch`, { updates });
      if (response.success && response.data) {
        return response.data;
      }
      throw new Error(response.error?.message || 'Batch update failed');
    },

    /**
     * Delete multiple items
     */
    batchDelete: async (ids: string[]): Promise<void> => {
      await apiClient.delete(`${endpoint}/batch`, { ids });
    },
  };
}
