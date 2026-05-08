/**
 * Error Type Definitions
 * Centralized types for error handling and recovery
 */

// ============================================
// Error Types
// ============================================

/**
 * Standard application error
 * Used for consistent error handling across the app
 */
export interface AppError extends Error {
  code?: string;
  status?: number;
  details?: Record<string, unknown>;
  isRetryable?: boolean;
  timestamp?: string;
}

/**
 * API error response
 * Returned by API endpoints on error
 */
export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  status: number;
  timestamp: string;
  requestId?: string;
}

/**
 * Validation error
 * Returned when input validation fails
 */
export interface ValidationErrorDetail {
  field: string;
  message: string;
  code?: string;
  value?: unknown;
}

/**
 * Network error
 * Represents network-related failures
 */
export interface NetworkError extends AppError {
  code: 'NETWORK_ERROR' | 'TIMEOUT' | 'OFFLINE';
  retryable: true;
}

/**
 * Authentication error
 * Represents auth-related failures
 */
export interface AuthError extends AppError {
  code: 'UNAUTHORIZED' | 'FORBIDDEN' | 'SESSION_EXPIRED';
  status: 401 | 403;
}

/**
 * Business logic error
 * Represents domain-specific failures
 */
export interface BusinessError extends AppError {
  code: string;
  status: 400 | 409 | 422;
  details: Record<string, unknown>;
}

// ============================================
// Error Handling Utilities
// ============================================

/**
 * Type guard to check if error is an AppError
 */
export function isAppError(error: unknown): error is AppError {
  return error instanceof Error && 'code' in error;
}

/**
 * Type guard to check if error is a network error
 */
export function isNetworkError(error: unknown): error is NetworkError {
  return isAppError(error) && 
    (error.code === 'NETWORK_ERROR' || 
     error.code === 'TIMEOUT' || 
     error.code === 'OFFLINE');
}

/**
 * Type guard to check if error is an auth error
 */
export function isAuthError(error: unknown): error is AuthError {
  return isAppError(error) && 
    (error.code === 'UNAUTHORIZED' || 
     error.code === 'FORBIDDEN' || 
     error.code === 'SESSION_EXPIRED');
}

/**
 * Type guard to check if error is a business error
 */
export function isBusinessError(error: unknown): error is BusinessError {
  return isAppError(error) && error.status === 400 || error.status === 409 || error.status === 422;
}

/**
 * Extract error message from unknown error
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  if (error && typeof error === 'object' && 'message' in error) {
    return String(error.message);
  }
  return 'An unknown error occurred';
}

/**
 * Extract error details from unknown error
 */
export function getErrorDetails(error: unknown): Record<string, unknown> {
  if (isAppError(error)) {
    return error.details || {};
  }
  if (error && typeof error === 'object') {
    return error as Record<string, unknown>;
  }
  return {};
}

/**
 * Check if error is retryable
 */
export function isRetryableError(error: unknown): boolean {
  if (isNetworkError(error)) {
    return true;
  }
  if (isAppError(error)) {
    return error.isRetryable === true;
  }
  return false;
}

// ============================================
// Error Recovery Types
// ============================================

/**
 * Error recovery strategy
 */
export type ErrorRecoveryStrategy = 
  | 'retry'
  | 'fallback'
  | 'user_action'
  | 'reload'
  | 'logout'
  | 'none';

/**
 * Error recovery context
 */
export interface ErrorRecoveryContext {
  error: Error;
  strategy: ErrorRecoveryStrategy;
  retryCount?: number;
  maxRetries?: number;
  fallbackValue?: unknown;
  userMessage?: string;
}

/**
 * Error recovery handler
 */
export type ErrorRecoveryHandler = (context: ErrorRecoveryContext) => Promise<void>;

/**
 * Error recovery result
 */
export interface ErrorRecoveryResult {
  recovered: boolean;
  strategy: ErrorRecoveryStrategy;
  error?: Error;
  message?: string;
}
