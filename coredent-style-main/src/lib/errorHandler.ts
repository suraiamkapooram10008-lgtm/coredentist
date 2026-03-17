// Global error handling utilities
import { logger } from './logger';

export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode?: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export class ValidationError extends AppError {
  constructor(message: string, details?: unknown) {
    super(message, 'VALIDATION_ERROR', 400, details);
    this.name = 'ValidationError';
  }
}

export class AuthenticationError extends AppError {
  constructor(message = 'Authentication required') {
    super(message, 'AUTHENTICATION_ERROR', 401);
    this.name = 'AuthenticationError';
  }
}

export class AuthorizationError extends AppError {
  constructor(message = 'Insufficient permissions') {
    super(message, 'AUTHORIZATION_ERROR', 403);
    this.name = 'AuthorizationError';
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, 'NOT_FOUND', 404);
    this.name = 'NotFoundError';
  }
}

export class NetworkError extends AppError {
  constructor(message = 'Network error occurred') {
    super(message, 'NETWORK_ERROR', 0);
    this.name = 'NetworkError';
  }
}

// Global error handler
export function handleError(error: unknown): AppError {
  if (error instanceof AppError) {
    logger.error(error.message, error, { code: error.code });
    return error;
  }

  if (error instanceof Error) {
    logger.error('Unexpected error', error);
    return new AppError(error.message, 'UNKNOWN_ERROR');
  }

  logger.error('Unknown error type', undefined, { error });
  return new AppError('An unexpected error occurred', 'UNKNOWN_ERROR');
}

// User-friendly error messages
export function getUserFriendlyMessage(error: AppError): string {
  const messages: Record<string, string> = {
    VALIDATION_ERROR: 'Please check your input and try again.',
    AUTHENTICATION_ERROR: 'Please sign in to continue.',
    AUTHORIZATION_ERROR: 'You don\'t have permission to perform this action.',
    NOT_FOUND: 'The requested resource was not found.',
    NETWORK_ERROR: 'Unable to connect. Please check your internet connection.',
    UNKNOWN_ERROR: 'Something went wrong. Please try again.',
  };

  return messages[error.code] || error.message;
}

// Setup global error handlers
export function setupGlobalErrorHandlers() {
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    logger.error('Unhandled promise rejection', event.reason);
    event.preventDefault();
  });

  // Handle global errors
  window.addEventListener('error', (event) => {
    logger.error('Global error', event.error, {
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    });
  });
}
