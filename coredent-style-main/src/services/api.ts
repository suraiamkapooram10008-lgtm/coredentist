import { toURLSearchParams } from '@/lib/utils';
import { getCsrfHeader } from '@/lib/csrf';
import { logger } from '@/lib/logger';

// ... existing imports ...
import type {
  LoginCredentials,
  LoginResponse,
  User,
  InvitationDetails,
  Patient,
  PatientListParams,
  PaginatedResponse,
  Appointment,
  AppointmentListParams,
  DentalChart,
  ClinicalNote,
  TreatmentPlan,
  Invoice,
  Payment,
  ReportParams,
  ProductionReport,
  AppointmentReport,
  ApiResponse,
  NotificationSummary,
} from '@/types/api';
import type { BillingPreferences } from '@/types/settings';

// ============================================
// Configuration
// ============================================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// ============================================
// HTTP Client
// ============================================

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;
  private isRefreshing = false;
  private refreshPromise: Promise<string | null> | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string | null) {
    this.token = token;
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retry = true
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const isFormData = options.body instanceof FormData;
    const headers: HeadersInit = {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...options.headers,
    };
    
    // CRIT-01/CRIT-06 FIX: Use Bearer token authentication for cross-origin deployment
    // Tokens are stored in memory only (NOT localStorage, NOT cookies)
    if (this.token) {
      Object.assign(headers, {
        'Authorization': `Bearer ${this.token}`,
      });
    }
    
    // Add CSRF token for state-changing requests
    if (options.method && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method)) {
      Object.assign(headers, getCsrfHeader());
    }

    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
        // FIX: Use 'include' for cross-origin cookie support (CSRF + refresh tokens)
        credentials: 'include',
      });
      
      clearTimeout(timeoutId);

      // Handle 401 Unauthorized - session expired
      // But skip token refresh for login endpoints (can't refresh when not logged in)
      if (response.status === 401 && !endpoint.includes('/auth/login')) {
        if (retry) {
          const newToken = await this.refreshAccessToken();
          if (newToken) {
            return this.request<T>(endpoint, options, false);
          }
        }
        this.token = null;
        // Note: Tokens are in httpOnly cookies - cannot clear from client
        // Logout will be handled by redirecting to login
        window.dispatchEvent(new CustomEvent('auth:logout'));
        logger.warn('Session expired, redirecting to login');
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login';
        }
        return {
          success: false,
          error: {
            code: 'UNAUTHORIZED',
            message: 'Your session has expired. Please sign in again.',
          },
        };
      }

      // For login endpoint with 401, return invalid credentials error
      if (response.status === 401 && endpoint.includes('/auth/login')) {
        const data = await response.json().catch(() => ({}));
        return {
          success: false,
          error: {
            code: 'INVALID_CREDENTIALS',
            message: data.message || 'Invalid credentials',
          },
        };
      }

      // Handle 403 Forbidden
      if (response.status === 403) {
        logger.warn('Access forbidden', { endpoint });
        return {
          success: false,
          error: {
            code: 'FORBIDDEN',
            message: 'You do not have permission to perform this action.',
          },
        };
      }

      const data = await response.json();

      if (!response.ok) {
        logger.error(`API error: ${endpoint}`, undefined, {
          endpoint,
          status: response.status,
          error: data,
        });
        return {
          success: false,
          error: {
            code: data.code || 'API_ERROR',
            message: data.message || 'An error occurred',
            details: data.details,
          },
        };
      }

      return {
        success: true,
        data: data as T,
      };
    } catch (error) {
      clearTimeout(timeoutId);
      
      // Handle timeout
      if (error instanceof Error && error.name === 'AbortError') {
        logger.error('Request timeout', error, { endpoint });
        return {
          success: false,
          error: {
            code: 'TIMEOUT_ERROR',
            message: 'Request timed out. Please try again.',
          },
        };
      }
      
      logger.error('Network error', error as Error, { endpoint });
      return {
        success: false,
        error: {
          code: 'NETWORK_ERROR',
          message: error instanceof Error ? error.message : 'Network error occurred',
        },
      };
    }
  }

  async get<T>(endpoint: string, params?: Record<string, unknown>): Promise<ApiResponse<T>> {
    let url = endpoint;
    if (params) {
      const queryString = toURLSearchParams(params).toString();
      if (queryString) {
        url += `?${queryString}`;
      }
    }
    return this.request<T>(url, { method: 'GET' });
  }

  async post<T>(endpoint: string, body?: unknown): Promise<ApiResponse<T>> {
    const requestBody = body instanceof FormData ? body : body ? JSON.stringify(body) : undefined;
    return this.request<T>(endpoint, {
      method: 'POST',
      body: requestBody,
    });
  }

  async put<T>(endpoint: string, body?: unknown): Promise<ApiResponse<T>> {
    const requestBody = body instanceof FormData ? body : body ? JSON.stringify(body) : undefined;
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: requestBody,
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  private async refreshAccessToken(): Promise<string | null> {
    // EXPERT HARDENING: Use JWT Rotation to prevent clinical session drops
    // We call the /auth/refresh endpoint which uses an HttpOnly cookie
    if (this.isRefreshing) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    this.refreshPromise = (async () => {
      try {
        // Create AbortController for timeout on refresh
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout for refresh

        const response = await fetch(`${this.baseUrl}/auth/refresh`, {
          method: 'POST',
          headers: {
             'Content-Type': 'application/json',
             ...getCsrfHeader() // CSRF required for state-changing refresh
          },
          // FIX: Use 'include' for cross-origin cookie support
          credentials: 'include',
          signal: controller.signal,
          body: JSON.stringify({
             // If we used Bearer for refresh, we'd pass it here
             // But the backend hardened version (Round 10) uses httpOnly cookies.
          })
        });

        clearTimeout(timeoutId);

        if (response.ok) {
          const result = await response.json();
          this.token = result.access_token;
          
          // EXPERT: Update CSRF if backend rotated it
          // getCsrfHeader will pick it up from cookie automatically
          
          return this.token;
        }
        
        return null;
      } catch (err) {
        // Handle timeout specifically
        if (err instanceof Error && err.name === 'AbortError') {
          logger.error('Token refresh timeout', err);
        } else {
          logger.error('Failed to rotate access token', err as Error);
        }
        return null;
      } finally {
        this.isRefreshing = false;
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }
}

export const apiClient = new ApiClient(API_BASE_URL);

// ============================================
// Auth API
// ============================================

export const authApi = {
  login: (credentials: LoginCredentials) => 
    apiClient.post<LoginResponse>('/auth/login', credentials),
  
  logout: () => 
    apiClient.post<void>('/auth/logout', {}), // Token from httpOnly cookie
  
  getCurrentUser: () => 
    apiClient.get<User>('/auth/me'),

  setToken: (token: string | null) =>
    apiClient.setToken(token),

  validateInvitation: (token: string) =>
    apiClient.get<InvitationDetails>('/auth/invitations/validate', { token }),

  acceptInvitation: (data: { token: string; password: string }) =>
    apiClient.post<void>('/auth/invitations/accept', data),

  requestPasswordReset: (data: { email: string }) =>
    apiClient.post<void>('/auth/forgot-password', data),

  resetPassword: (data: { token: string; password: string }) =>
    apiClient.post<void>('/auth/reset-password', data),
};

export const settingsApi = {
  getBillingPreferences: () =>
    apiClient.get<BillingPreferences>('/settings/billing'),

  updateBillingPreferences: (data: BillingPreferences) =>
    apiClient.put<BillingPreferences>('/settings/billing', data),
};

export const notificationsApi = {
  getUnreadCount: () =>
    apiClient.get<NotificationSummary>('/notifications/unread-count'),
};

// ============================================
// Patients API
// ============================================

export const patientsApi = {
  list: (params?: PatientListParams) => 
    apiClient.get<PaginatedResponse<Patient>>('/patients', params as unknown as Record<string, unknown>),
  
  getById: (id: string) => 
    apiClient.get<Patient>(`/patients/${id}`),
  
  create: (patient: Omit<Patient, 'id' | 'createdAt' | 'updatedAt'>) => 
    apiClient.post<Patient>('/patients', patient),
  
  update: (id: string, patient: Partial<Patient>) => 
    apiClient.put<Patient>(`/patients/${id}`, patient),
  
  delete: (id: string) => 
    apiClient.delete<void>(`/patients/${id}`),
};

// ============================================
// Appointments API
// ============================================

export const appointmentsApi = {
  list: (params: AppointmentListParams) => 
    apiClient.get<Appointment[]>('/appointments', params as unknown as Record<string, unknown>),
  
  getById: (id: string) => 
    apiClient.get<Appointment>(`/appointments/${id}`),
  
  create: (appointment: Omit<Appointment, 'id' | 'createdAt' | 'updatedAt'>) => 
    apiClient.post<Appointment>('/appointments', appointment),
  
  update: (id: string, appointment: Partial<Appointment>) => 
    apiClient.put<Appointment>(`/appointments/${id}`, appointment),
  
  delete: (id: string) => 
    apiClient.delete<void>(`/appointments/${id}`),
};

// ============================================
// Dental Chart API
// ============================================

export const dentalChartApi = {
  getByPatientId: (patientId: string) => 
    apiClient.get<DentalChart>(`/patients/${patientId}/chart`),
  
  update: (patientId: string, chart: Partial<DentalChart>) => 
    apiClient.put<DentalChart>(`/patients/${patientId}/chart`, chart),
};

// ============================================
// Clinical Notes API
// ============================================

export const clinicalNotesApi = {
  listByPatient: (patientId: string) => 
    apiClient.get<ClinicalNote[]>(`/patients/${patientId}/notes`),
  
  getById: (id: string) => 
    apiClient.get<ClinicalNote>(`/notes/${id}`),
  
  create: (note: Omit<ClinicalNote, 'id' | 'createdAt' | 'updatedAt'>) => 
    apiClient.post<ClinicalNote>('/notes', note),
  
  update: (id: string, note: Partial<ClinicalNote>) => 
    apiClient.put<ClinicalNote>(`/notes/${id}`, note),
};

// ============================================
// Treatment Plans API
// ============================================

export const treatmentPlansApi = {
  listByPatient: (patientId: string) => 
    apiClient.get<TreatmentPlan[]>(`/patients/${patientId}/treatment-plans`),
  
  getById: (id: string) => 
    apiClient.get<TreatmentPlan>(`/treatment-plans/${id}`),
  
  create: (plan: Omit<TreatmentPlan, 'id' | 'createdAt' | 'updatedAt'>) => 
    apiClient.post<TreatmentPlan>('/treatment-plans', plan),
  
  update: (id: string, plan: Partial<TreatmentPlan>) => 
    apiClient.put<TreatmentPlan>(`/treatment-plans/${id}`, plan),
};

// ============================================
// Billing API
// ============================================

export const billingApi = {
  listInvoices: (patientId?: string) => 
    apiClient.get<Invoice[]>('/invoices', { patientId }),
  
  getInvoice: (id: string) => 
    apiClient.get<Invoice>(`/invoices/${id}`),
  
  createInvoice: (invoice: Omit<Invoice, 'id' | 'createdAt' | 'updatedAt'>) => 
    apiClient.post<Invoice>('/invoices', invoice),
  
  createPayment: (payment: Omit<Payment, 'id'>) => 
    apiClient.post<Payment>('/payments', payment),
  
  getPatientLedger: (patientId: string) => 
    apiClient.get<{ invoices: Invoice[]; payments: Payment[] }>(`/patients/${patientId}/ledger`),
};

// ============================================
// Reports API
// ============================================

export const reportsApi = {
  getProduction: (params: ReportParams) => 
    apiClient.get<ProductionReport>('/reports/production', params as unknown as Record<string, unknown>),
  
  getAppointments: (params: ReportParams) => 
    apiClient.get<AppointmentReport>('/reports/appointments', params as unknown as Record<string, unknown>),
};
