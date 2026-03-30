// Centralized logging and error tracking

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  context?: Record<string, unknown>;
  error?: Error;
}

// Error monitoring integration using Sentry.
// Initialize Sentry in production if DSN is provided.
import * as Sentry from '@sentry/browser';
if (!import.meta.env.DEV && import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.MODE,
    tracesSampleRate: 0.1,
  });
}

class Logger {
  private get isDevelopment(): boolean {
    return import.meta.env.DEV;
  }
  private logs: LogEntry[] = [];
  private maxLogs = 100;

  private createEntry(
    level: LogLevel,
    message: string,
    context?: Record<string, unknown>,
    error?: Error
  ): LogEntry {
    return {
      level,
      message,
      timestamp: new Date().toISOString(),
      context,
      error,
    };
  }

  private addLog(entry: LogEntry) {
    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }
  }

  private sendToMonitoring(entry: LogEntry) {
    // Send error logs to monitoring endpoint regardless of environment (required for tests)
    if (entry.level === 'error') {
      // Disabled for now - backend doesn't have /api/logs endpoint
      // Use globalThis.fetch to ensure mocked fetch is used in tests
      // globalThis.fetch('/api/logs', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(entry),
      // }).catch(() => {
      //   // Silently fail if logging endpoint is unavailable
      // });
    }
  }

  debug(message: string, context?: Record<string, unknown>) {
    const entry = this.createEntry('debug', message, context);
    this.addLog(entry);
    
    if (this.isDevelopment) {
      // eslint-disable-next-line no-console
      console.debug(`[DEBUG] ${message}`, context);
    }
  }

  info(message: string, context?: Record<string, unknown>) {
    const entry = this.createEntry('info', message, context);
    this.addLog(entry);
    
    if (this.isDevelopment) {
      console.info(`[INFO] ${message}`, context);
    }
  }

  warn(message: string, context?: Record<string, unknown>) {
    const entry = this.createEntry('warn', message, context);
    this.addLog(entry);
    
    // eslint-disable-next-line no-console
    console.warn(`[WARN] ${message}`, context);
    this.sendToMonitoring(entry);
  }

  error(message: string, error?: Error, context?: Record<string, unknown>) {
    const entry = this.createEntry('error', message, context, error);
    this.addLog(entry);
    
    console.error(`[ERROR] ${message}`, error, context);
    this.sendToMonitoring(entry);
  }

  // Get recent logs for debugging
  getRecentLogs(count = 50): LogEntry[] {
    return this.logs.slice(-count);
  }

  // Clear logs
  clearLogs() {
    this.logs = [];
  }

  // Export logs for support
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }
}

export const logger = new Logger();

// Error boundary helper
export function logError(error: Error, errorInfo?: { componentStack?: string }) {
  logger.error('React Error Boundary caught an error', error, {
    componentStack: errorInfo?.componentStack,
  });
}

// API error helper
export function logApiError(
  endpoint: string,
  error: Error,
  context?: Record<string, unknown>
) {
  logger.error(`API Error: ${endpoint}`, error, {
    endpoint,
    ...context,
  });
}

// Performance monitoring
export function logPerformance(metric: string, duration: number) {
  logger.info(`Performance: ${metric}`, { duration, metric });
}
