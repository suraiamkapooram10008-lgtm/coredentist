// CSRF Protection
// Implements CSRF token management for API requests
// CRIT-05 FIX: Added token expiration and strengthened storage practices.

const CSRF_TOKEN_KEY = 'csrf_token';
const CSRF_EXPIRES_AT_KEY = 'csrf_expires_at';
const CSRF_HEADER_NAME = 'X-CSRF-Token';
const CSRF_TOKEN_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours (matches backend cookie max_age)

/**
 * Gets the current CSRF token from sessionStorage
 * @returns CSRF token string or null if expired/missing
 */
export function getCsrfToken(): string | null {
  const expiresAt = sessionStorage.getItem(CSRF_EXPIRES_AT_KEY);
  if (expiresAt) {
    const expiry = parseInt(expiresAt, 10);
    if (Date.now() > expiry) {
      // Token expired - clear it
      clearCsrfToken();
      return null;
    }
  }
  return sessionStorage.getItem(CSRF_TOKEN_KEY);
}

/**
 * Sets a new CSRF token with expiration
 * @param token - Token string to set
 */
export function setCsrfToken(token: string): void {
  try {
    sessionStorage.setItem(CSRF_TOKEN_KEY, token);
    sessionStorage.setItem(CSRF_EXPIRES_AT_KEY, String(Date.now() + CSRF_TOKEN_TTL_MS));
  } catch {
    // sessionStorage may be unavailable in private mode or if disabled
    // In that case, the token will be lost on refresh but CSRF protection
    // still works during the current session via the httpOnly cookie
  }
}

/**
 * Clears the CSRF token and its expiration
 */
export function clearCsrfToken(): void {
  try {
    sessionStorage.removeItem(CSRF_TOKEN_KEY);
    sessionStorage.removeItem(CSRF_EXPIRES_AT_KEY);
  } catch {
    // Ignore errors if storage is unavailable
  }
}

/**
 * Gets CSRF header object for fetch requests
 * @returns Object with CSRF header (empty if no valid token)
 */
export function getCsrfHeader(): Record<string, string> {
  const token = getCsrfToken();
  if (!token) {
    return {};
  }
  return {
    [CSRF_HEADER_NAME]: token,
  };
}

/**
 * Validates CSRF token from response against stored token
 * @param responseToken - Token from API response
 * @returns True if token matches current stored token
 */
export function validateCsrfToken(responseToken: string): boolean {
  const currentToken = getCsrfToken();
  return currentToken === responseToken;
}

/**
 * Refreshes CSRF token (call after login)
 * Resets expiration timer to full TTL.
 */
export function refreshCsrfToken(token: string): void {
  setCsrfToken(token);
}

/**
 * Gets the CSRF header name
 * @returns Header name string
 */
export function getCsrfHeaderName(): string {
  return CSRF_HEADER_NAME;
}
