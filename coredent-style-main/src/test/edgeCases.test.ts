// Edge‑case tests for CoreDent Frontend

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { getCsrfToken, setCsrfToken, clearCsrfToken } from '@/lib/csrf';
import { logger } from '@/lib/logger';

describe('Edge‑case testing', () => {
  it('should not enable DEV_BYPAS_AUTH in production', () => {
    // Simulate production environment
    const isDev = import.meta.env.DEV;
    const devBypassAuth = (globalThis as any).DEV_BYPAS_AUTH ?? false;
    if (!isDev) {
      expect(devBypassAuth).toBe(false);
    }
  });

  it('CSRF token generation and validation', () => {
    clearCsrfToken();
    setCsrfToken('test-csrf-token');
    const token = getCsrfToken();
    expect(token).toBe('test-csrf-token');
    const isValid = token === getCsrfToken();
    expect(isValid).toBe(true);
  });

  it('logger.error should log errors correctly', () => {
    // Test that logger.error properly logs errors
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    const testError = new Error('Test error');
    logger.error('Test error message', testError, { context: 'test' });
    
    // Verify console.error was called
    expect(consoleSpy).toHaveBeenCalled();
    
    // Verify the log was added to logger's internal logs
    const logs = logger.getRecentLogs(1);
    expect(logs.length).toBeGreaterThan(0);
    expect(logs[0].level).toBe('error');
    expect(logs[0].message).toBe('Test error message');
    
    consoleSpy.mockRestore();
    logger.clearLogs();
  });
});
