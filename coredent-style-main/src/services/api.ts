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
    
    // SECURITY: Use httpOnly cookies for authentication (set by backend)
    // No need to set Authorization header - cookies are sent automatically
    
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
        credentials: 'include', // SECURITY: Send cookies with request
      });
      
      clearTimeout(timeoutId);

      // Handle 401 Unauthorized - session expired
      if (response.status === 401) {
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
    // SECURITY: Use httpOnly cookies - refresh token is sent automatically
    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getCsrfHeader(),
        },
        body: JSON.stringify({}), // Token from cookie
        credentials: 'include', // SECURITY: Send cookies
      });
      
      if (!response.ok) {
        return null;
      }
      
      // Tokens are in httpOnly cookies - no need to store them
      return 'token_from_cookie';
    } catch {
      return null;
    }
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
