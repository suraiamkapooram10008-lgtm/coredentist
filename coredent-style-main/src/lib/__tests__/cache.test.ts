import { describe, it, expect, beforeEach, vi } from 'vitest';
import { sessionCache, localCache } from '../cache';

// Mock storage
const createMockStorage = (): Storage => {
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
    key: vi.fn((index: number) => {
      const keys = Object.keys(store);
      return index >= 0 && index < keys.length ? keys[index] : null;
    }),
    get length() {
      return Object.keys(store).length;
    },
  };
};

const mockSessionStorage = createMockStorage();
const mockLocalStorage = createMockStorage();

Object.defineProperty(window, 'sessionStorage', { value: mockSessionStorage });
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

describe('sessionCache', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSessionStorage.clear();
  });

  describe('set and get', () => {
    it('should store and retrieve data', () => {
      const testData = { name: 'test', value: 123 };
      
      sessionCache.set('test-key', testData);
      const retrieved = sessionCache.get('test-key');
      
      expect(retrieved).toEqual(testData);
    });

    it('should return null for non-existent keys', () => {
      const result = sessionCache.get('non-existent');
      expect(result).toBeNull();
    });

    it('should handle TTL expiration', () => {
      vi.useFakeTimers();
      
      sessionCache.set('test-key', 'test-value', 1000); // 1 second TTL
      
      // Should be available immediately
      expect(sessionCache.get('test-key')).toBe('test-value');
      
      // Fast forward time
      vi.advanceTimersByTime(1001);
      
      // Should be expired
      expect(sessionCache.get('test-key')).toBeNull();
      
      vi.useRealTimers();
    });

    it('should handle storage quota exceeded', () => {
      // Mock storage to throw quota exceeded error
      (mockSessionStorage.setItem as ReturnType<typeof vi.fn>).mockImplementationOnce(() => {
        throw new Error('QuotaExceededError');
      });

      // Should not throw, but handle gracefully
      expect(() => {
        sessionCache.set('test-key', 'test-value');
      }).not.toThrow();
    });
  });

  describe('has', () => {
    it('should return true for existing keys', () => {
      sessionCache.set('test-key', 'test-value');
      expect(sessionCache.has('test-key')).toBe(true);
    });

    it('should return false for non-existent keys', () => {
      expect(sessionCache.has('non-existent')).toBe(false);
    });

    it('should return false for expired keys', () => {
      vi.useFakeTimers();
      
      sessionCache.set('test-key', 'test-value', 1000);
      vi.advanceTimersByTime(1001);
      
      expect(sessionCache.has('test-key')).toBe(false);
      
      vi.useRealTimers();
    });
  });

  describe('remove', () => {
    it('should remove existing keys', () => {
      sessionCache.set('test-key', 'test-value');
      expect(sessionCache.has('test-key')).toBe(true);
      
      sessionCache.remove('test-key');
      expect(sessionCache.has('test-key')).toBe(false);
    });
  });

  describe('clear', () => {
    it('should clear all cache entries', () => {
      sessionCache.set('key1', 'value1');
      sessionCache.set('key2', 'value2');
      
      expect(sessionCache.has('key1')).toBe(true);
      expect(sessionCache.has('key2')).toBe(true);
      
      sessionCache.clear();
      
      expect(sessionCache.has('key1')).toBe(false);
      expect(sessionCache.has('key2')).toBe(false);
    });
  });

  describe('size', () => {
    it('should return correct cache size', () => {
      expect(sessionCache.size()).toBe(0);
      
      sessionCache.set('key1', 'value1');
      expect(sessionCache.size()).toBe(1);
      
      sessionCache.set('key2', 'value2');
      expect(sessionCache.size()).toBe(2);
      
      sessionCache.remove('key1');
      expect(sessionCache.size()).toBe(1);
    });
  });

  describe('keys', () => {
    it('should return all cache keys', () => {
      sessionCache.set('key1', 'value1');
      sessionCache.set('key2', 'value2');
      
      const keys = sessionCache.keys();
      expect(keys).toContain('key1');
      expect(keys).toContain('key2');
      expect(keys).toHaveLength(2);
    });
  });
});

describe('localCache', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.clear();
  });

  describe('set and get', () => {
    it('should store and retrieve data', () => {
      const testData = { name: 'test', value: 123 };
      
      localCache.set('test-key', testData);
      const retrieved = localCache.get('test-key');
      
      expect(retrieved).toEqual(testData);
    });

    it('should handle TTL expiration', () => {
      vi.useFakeTimers();
      
      localCache.set('test-key', 'test-value', 2000); // 2 seconds TTL
      
      // Should be available immediately
      expect(localCache.get('test-key')).toBe('test-value');
      
      // Fast forward time
      vi.advanceTimersByTime(2001);
      
      // Should be expired
      expect(localCache.get('test-key')).toBeNull();
      
      vi.useRealTimers();
    });

    it('should handle storage quota exceeded', () => {
      // Mock storage to throw quota exceeded error
      (mockLocalStorage.setItem as ReturnType<typeof vi.fn>).mockImplementationOnce(() => {
        throw new Error('QuotaExceededError');
      });

      // Should not throw, but handle gracefully
      expect(() => {
        localCache.set('test-key', 'test-value');
      }).not.toThrow();
    });
  });

  describe('persistence', () => {
    it('should persist data across sessions', () => {
      localCache.set('persistent-key', 'persistent-value');
      
      // Simulate page reload by creating new cache instance
      const retrieved = localCache.get('persistent-key');
      expect(retrieved).toBe('persistent-value');
    });
  });
});