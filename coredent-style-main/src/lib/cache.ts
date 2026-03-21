// Advanced caching utilities for optimized data management

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

interface CacheOptions {
  ttl?: number; // Time to live in milliseconds
  maxSize?: number; // Maximum cache size
}

class MemoryCache {
  private cache: Map<string, CacheEntry<any>> = new Map();
  private maxSize: number;

  constructor(maxSize = 100) {
    this.maxSize = maxSize;
  }

  set<T>(key: string, data: T, ttl = 5 * 60 * 1000): void {
    // Evict oldest entries if cache is full
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }

    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      expiresAt: Date.now() + ttl,
    };

    this.cache.set(key, entry);
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) {
      return null;
    }

    // Check if expired
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  has(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) return false;

    // Check if expired
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return false;
    }

    return true;
  }

  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }

  size(): number {
    return this.cache.size;
  }

  // Get all valid (non-expired) keys
  keys(): string[] {
    const now = Date.now();
    const validKeys: string[] = [];

    for (const [key, entry] of this.cache.entries()) {
      if (now <= entry.expiresAt) {
        validKeys.push(key);
      } else {
        this.cache.delete(key);
      }
    }

    return validKeys;
  }
}

// Global cache instances
export const apiCache = new MemoryCache(200);
export const uiCache = new MemoryCache(50);

// Cache decorator for functions
export function cached<T extends (...args: any[]) => any>(
  fn: T,
  options: CacheOptions = {}
): T {
  const { ttl = 5 * 60 * 1000 } = options;
  const cache = new Map<string, CacheEntry<ReturnType<T>>>();

  return ((...args: Parameters<T>): ReturnType<T> => {
    const key = JSON.stringify(args);
    const cached = cache.get(key);

    if (cached && Date.now() <= cached.expiresAt) {
      return cached.data;
    }

    const result = fn(...args);

    // Handle promises
    if (result instanceof Promise) {
      return result.then((data) => {
        cache.set(key, {
          data,
          timestamp: Date.now(),
          expiresAt: Date.now() + ttl,
        });
        return data;
      }) as ReturnType<T>;
    }

    cache.set(key, {
      data: result,
      timestamp: Date.now(),
      expiresAt: Date.now() + ttl,
    });

    return result;
  }) as T;
}

// Memoization with LRU eviction
export class LRUCache<K, V> {
  private maxSize: number;
  private cache: Map<K, V>;

  constructor(maxSize = 100) {
    this.maxSize = maxSize;
    this.cache = new Map();
  }

  get(key: K): V | undefined {
    if (!this.cache.has(key)) {
      return undefined;
    }

    // Move to end (most recently used)
    const value = this.cache.get(key)!;
    this.cache.delete(key);
    this.cache.set(key, value);

    return value;
  }

  set(key: K, value: V): void {
    // Delete if exists (to update position)
    if (this.cache.has(key)) {
      this.cache.delete(key);
    }

    // Evict least recently used if at capacity
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }

    this.cache.set(key, value);
  }

  has(key: K): boolean {
    return this.cache.has(key);
  }

  delete(key: K): boolean {
    return this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }

  size(): number {
    return this.cache.size;
  }
}

// Session storage cache with expiration
export const sessionCache = {
  set<T>(key: string, data: T, ttl = 30 * 60 * 1000): void {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      expiresAt: Date.now() + ttl,
    };

    try {
      sessionStorage.setItem(key, JSON.stringify(entry));
    } catch (error) {
      if (import.meta.env.DEV) {
        console.warn('Session storage full, clearing old entries');
      }
      this.clear();
      sessionStorage.setItem(key, JSON.stringify(entry));
    }
  },

  get<T>(key: string): T | null {
    try {
      const item = sessionStorage.getItem(key);
      if (!item) return null;

      const entry: CacheEntry<T> = JSON.parse(item);

      if (Date.now() > entry.expiresAt) {
        sessionStorage.removeItem(key);
        return null;
      }

      return entry.data;
    } catch {
      return null;
    }
  },

  has(key: string): boolean {
    try {
      const item = sessionStorage.getItem(key);
      if (!item) return false;

      const entry: CacheEntry<any> = JSON.parse(item);
      if (Date.now() > entry.expiresAt) {
        sessionStorage.removeItem(key);
        return false;
      }

      return true;
    } catch {
      return false;
    }
  },

  remove(key: string): void {
    sessionStorage.removeItem(key);
  },

  delete(key: string): void {
    sessionStorage.removeItem(key);
  },

  clear(): void {
    sessionStorage.clear();
  },

  size(): number {
    let count = 0;
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key) {
        try {
          const item = sessionStorage.getItem(key);
          if (item) {
            const entry = JSON.parse(item) as { expiresAt: number };
            if (Date.now() <= entry.expiresAt) {
              count++;
            }
          }
        } catch {
          // Ignore parse errors
        }
      }
    }
    return count;
  },

  keys(): string[] {
    const validKeys: string[] = [];
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key) {
        try {
          const item = sessionStorage.getItem(key);
          if (item) {
            const entry = JSON.parse(item) as { expiresAt: number };
            if (Date.now() <= entry.expiresAt) {
              validKeys.push(key);
            }
          }
        } catch {
          // Ignore parse errors
        }
      }
    }
    return validKeys;
  },
};

// Local storage cache with expiration
// SECURITY WARNING: Avoid storing PHI (Protected Health Information) or sensitive data
// in localStorage as it's accessible via XSS attacks. Use sessionCache for sensitive data.
export const localCache = {
  set<T>(key: string, data: T, ttl = 24 * 60 * 60 * 1000): void {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      expiresAt: Date.now() + ttl,
    };

    try {
      localStorage.setItem(key, JSON.stringify(entry));
    } catch (error) {
      if (import.meta.env.DEV) {
        console.warn('Local storage full, clearing old entries');
      }
      this.clear();
      localStorage.setItem(key, JSON.stringify(entry));
    }
  },

  get<T>(key: string): T | null {
    try {
      const item = localStorage.getItem(key);
      if (!item) return null;

      const entry: CacheEntry<T> = JSON.parse(item);

      if (Date.now() > entry.expiresAt) {
        localStorage.removeItem(key);
        return null;
      }

      return entry.data;
    } catch {
      return null;
    }
  },

  delete(key: string): void {
    localStorage.removeItem(key);
  },

  clear(): void {
    localStorage.clear();
  },
};
