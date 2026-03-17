import { describe, it, expect, beforeEach, vi } from 'vitest';
import { logger, logError, logApiError, logPerformance } from '../logger';

// Mock fetch for monitoring endpoint
global.fetch = vi.fn();

describe('logger', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    logger.clearLogs();
    // Mock development environment
    vi.stubEnv('DEV', true);
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  describe('debug', () => {
    it('should log debug messages in development', () => {
      const consoleSpy = vi.spyOn(console, 'debug').mockImplementation(() => {});
      
      logger.debug('Debug message', { key: 'value' });
      
      expect(consoleSpy).toHaveBeenCalledWith('[DEBUG] Debug message', { key: 'value' });
      
      const logs = logger.getRecentLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0]).toMatchObject({
        level: 'debug',
        message: 'Debug message',
        context: { key: 'value' },
      });
      
      consoleSpy.mockRestore();
    });

    it('should not log to console in production', () => {
      vi.stubEnv('DEV', false);
      const consoleSpy = vi.spyOn(console, 'debug').mockImplementation(() => {});
      
      logger.debug('Debug message');
      
      expect(consoleSpy).not.toHaveBeenCalled();
      
      // Should still add to logs
      const logs = logger.getRecentLogs();
      expect(logs).toHaveLength(1);
      
      consoleSpy.mockRestore();
    });
  });

  describe('info', () => {
    it('should log info messages', () => {
      const consoleSpy = vi.spyOn(console, 'info').mockImplementation(() => {});
      
      logger.info('Info message', { data: 'test' });
      
      expect(consoleSpy).toHaveBeenCalledWith('[INFO] Info message', { data: 'test' });
      
      const logs = logger.getRecentLogs();
      expect(logs[0]).toMatchObject({
        level: 'info',
        message: 'Info message',
      });
      
      consoleSpy.mockRestore();
    });
  });

  describe('warn', () => {
    it('should log warnings and send to monitoring', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      
      logger.warn('Warning message', { warning: 'data' });
      
      expect(consoleSpy).toHaveBeenCalledWith('[WARN] Warning message', { warning: 'data' });
      expect(fetch).toHaveBeenCalledWith('/api/logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: expect.stringContaining('"level":"warn"'),
      });
      
      consoleSpy.mockRestore();
    });
  });

  describe('error', () => {
    it('should log errors and send to monitoring', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const testError = new Error('Test error');
      
      logger.error('Error message', testError, { context: 'test' });
      
      expect(consoleSpy).toHaveBeenCalledWith('[ERROR] Error message', testError, { context: 'test' });
      expect(fetch).toHaveBeenCalledWith('/api/logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: expect.stringContaining('"level":"error"'),
      });
      
      const logs = logger.getRecentLogs();
      expect(logs[0]).toMatchObject({
        level: 'error',
        message: 'Error message',
        error: testError,
        context: { context: 'test' },
      });
      
      consoleSpy.mockRestore();
    });
  });

  describe('log management', () => {
    it('should limit log entries to maxLogs', () => {
      // Add more than maxLogs entries
      for (let i = 0; i < 150; i++) {
        logger.info(`Message ${i}`);
      }
      
      const logs = logger.getRecentLogs();
      expect(logs.length).toBeLessThanOrEqual(100); // maxLogs is 100
    });

    it('should return recent logs with specified count', () => {
      for (let i = 0; i < 10; i++) {
        logger.info(`Message ${i}`);
      }
      
      const recentLogs = logger.getRecentLogs(5);
      expect(recentLogs).toHaveLength(5);
      expect(recentLogs[4].message).toBe('Message 9'); // Most recent
    });

    it('should clear all logs', () => {
      logger.info('Test message');
      expect(logger.getRecentLogs()).toHaveLength(1);
      
      logger.clearLogs();
      expect(logger.getRecentLogs()).toHaveLength(0);
    });

    it('should export logs as JSON', () => {
      logger.info('Test message', { data: 'test' });
      
      const exported = logger.exportLogs();
      const parsed = JSON.parse(exported);
      
      expect(parsed).toHaveLength(1);
      expect(parsed[0]).toMatchObject({
        level: 'info',
        message: 'Test message',
        context: { data: 'test' },
      });
    });
  });

  describe('helper functions', () => {
    it('should log React errors with logError', () => {
      const loggerSpy = vi.spyOn(logger, 'error');
      const testError = new Error('React error');
      const errorInfo = { componentStack: 'Component stack trace' };
      
      logError(testError, errorInfo);
      
      expect(loggerSpy).toHaveBeenCalledWith(
        'React Error Boundary caught an error',
        testError,
        { componentStack: 'Component stack trace' }
      );
    });

    it('should log API errors with logApiError', () => {
      const loggerSpy = vi.spyOn(logger, 'error');
      const testError = new Error('API error');
      
      logApiError('/api/test', testError, { status: 500 });
      
      expect(loggerSpy).toHaveBeenCalledWith(
        'API Error: /api/test',
        testError,
        { endpoint: '/api/test', status: 500 }
      );
    });

    it('should log performance metrics with logPerformance', () => {
      const loggerSpy = vi.spyOn(logger, 'info');
      
      logPerformance('api_call', 1500);
      
      expect(loggerSpy).toHaveBeenCalledWith(
        'Performance: api_call',
        { duration: 1500, metric: 'api_call' }
      );
    });
  });

  describe('monitoring integration', () => {
    it('should handle fetch errors gracefully', () => {
      (fetch as any).mockRejectedValueOnce(new Error('Network error'));
      
      expect(() => {
        logger.error('Test error');
      }).not.toThrow();
    });

    it('should only send error logs to monitoring', () => {
      logger.info('Info message');
      logger.warn('Warning message');
      logger.error('Error message');
      
      // Only error should trigger fetch
      expect(fetch).toHaveBeenCalledTimes(2); // warn and error both send to monitoring
    });
  });
});