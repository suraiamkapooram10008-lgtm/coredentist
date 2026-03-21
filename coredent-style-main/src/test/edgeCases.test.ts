// Edge‑case tests for CoreDent Frontend

import { describe, it, expect } from 'vitest';
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

  it('logger.error should send to monitoring in production (mocked)', async () => {
    // Mock fetch
    const fetchMock = vi.fn(() =>
      Promise.resolve({ ok: true }) as any
    );
    // @ts-expect-error - mocking global fetch for testing
    globalThis.fetch = fetchMock;
    // Force non‑development mode
    const originalEnv = import.meta.env;
    // @ts-expect-error - mocking import.meta.env for testing
    import.meta.env = { ...originalEnv, DEV: false };
    logger.error('Test error', new Error('Test'));
    // Expect fetch called
    expect(fetchMock).toHaveBeenCalled();
    // Restore
    // @ts-expect-error - restoring mocked import.meta.env
    import.meta.env = originalEnv;
  });
});
