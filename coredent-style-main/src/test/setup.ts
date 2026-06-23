// ============================================
// CoreDent PMS - Test Setup
// Global test configuration and mocks
// ============================================

import '@testing-library/jest-dom';
import { vi, beforeAll, afterEach, afterAll } from 'vitest';
import { cleanup } from '@testing-library/react';
import { server } from './mocks/server';

// Ensure API requests use relative paths so MSW handlers match
vi.stubEnv('VITE_API_BASE_URL', '/api/v1');

// ============================================
// MSW Server Setup
// ============================================

// Start server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));

// Reset handlers after each test
afterEach(() => server.resetHandlers());

// Clean up after all tests
afterAll(() => server.close());

// ============================================
// DOM Cleanup (React Testing Library)
// ============================================

// Unmount any rendered components after each test to avoid DOM/state leaks
afterEach(() => cleanup());

// ============================================
// Global Mocks
// ============================================

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock scrollTo
window.scrollTo = vi.fn();

// jsdom does not implement these Element methods; Radix UI relies on them.
window.HTMLElement.prototype.scrollIntoView = vi.fn();
window.HTMLElement.prototype.hasPointerCapture = vi.fn(() => false);
window.HTMLElement.prototype.releasePointerCapture = vi.fn();
window.HTMLElement.prototype.setPointerCapture = vi.fn();

// Mock sessionStorage
const mockSessionStorage = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'sessionStorage', {
  value: mockSessionStorage,
});

// Mock localStorage
const mockLocalStorage = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// ============================================
// Custom Matchers
// ============================================

expect.extend({
  toBeValidDate(received: unknown) {
    const pass = received instanceof Date && !isNaN(received.getTime());
    return {
      pass,
      message: () =>
        pass
          ? `expected ${received} not to be a valid date`
          : `expected ${received} to be a valid date`,
    };
  },
  toBeWithinRange(received: number, floor: number, ceiling: number) {
    const pass = received >= floor && received <= ceiling;
    return {
      pass,
      message: () =>
        pass
          ? `expected ${received} not to be within range ${floor} - ${ceiling}`
          : `expected ${received} to be within range ${floor} - ${ceiling}`,
    };
  },
});
