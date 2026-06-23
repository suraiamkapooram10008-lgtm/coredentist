import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { apiCache, uiCache, cached, LRUCache, sessionCache } from '../cache';

describe('MemoryCache (apiCache/uiCache)', () => {
  beforeEach(() => {
    apiCache.clear();
    uiCache.clear();
  });

  it('set and get a value', () => {
    apiCache.set('k', 42);
    expect(apiCache.get('k')).toBe(42);
  });

  it('returns null for a missing key', () => {
    expect(apiCache.get('nope')).toBeNull();
  });

  it('returns null and evicts when expired', () => {
    vi.useFakeTimers();
    apiCache.set('k', 'value', 100);
    expect(apiCache.get('k')).toBe('value');
    vi.advanceTimersByTime(150);
    expect(apiCache.get('k')).toBeNull();
    expect(apiCache.has('k')).toBe(false);
    vi.useRealTimers();
  });

  it('has returns false for expired entries', () => {
    vi.useFakeTimers();
    apiCache.set('k', 'value', 100);
    expect(apiCache.has('k')).toBe(true);
    vi.advanceTimersByTime(150);
    expect(apiCache.has('k')).toBe(false);
    vi.useRealTimers();
  });

  it('delete removes an entry and returns a boolean', () => {
    apiCache.set('k', 'value');
    expect(apiCache.delete('k')).toBe(true);
    expect(apiCache.delete('k')).toBe(false);
  });

  it('clear empties the cache', () => {
    apiCache.set('a', 1);
    apiCache.set('b', 2);
    expect(apiCache.size()).toBe(2);
    apiCache.clear();
    expect(apiCache.size()).toBe(0);
  });

  it('evicts the oldest entry when at capacity', () => {
    const small = new (apiCache.constructor as new (n: number) => typeof apiCache)(2);
    small.set('a', 1);
    small.set('b', 2);
    small.set('c', 3);
    expect(small.get('a')).toBeNull();
    expect(small.get('b')).toBe(2);
    expect(small.get('c')).toBe(3);
  });

  it('keys returns only non-expired keys and prunes expired ones', () => {
    vi.useFakeTimers();
    apiCache.set('a', 1, 100);
    apiCache.set('b', 2, 200);
    vi.advanceTimersByTime(150);
    const keys = apiCache.keys();
    expect(keys).toEqual(['b']);
    vi.useRealTimers();
  });
});

describe('cached()', () => {
  afterEach(() => vi.useRealTimers());

  it('memoizes sync return values by JSON-stringified args', () => {
    const fn = vi.fn((a: number) => a + 1);
    const memo = cached(fn as unknown as (...args: unknown[]) => unknown);
    expect(memo(1)).toBe(2);
    expect(memo(1)).toBe(2);
    expect(fn).toHaveBeenCalledOnce();
    expect(memo(2)).toBe(3);
    expect(fn).toHaveBeenCalledTimes(2);
  });

  it('caches the resolved value of an async function', async () => {
    const fn = vi.fn(async (a: number) => a * 2);
    const memo = cached(fn as unknown as (...args: unknown[]) => unknown);
    expect(await memo(5)).toBe(10);
    expect(await memo(5)).toBe(10);
    expect(fn).toHaveBeenCalledOnce();
  });

  it('expires memoized values after the TTL', async () => {
    vi.useFakeTimers();
    const fn = vi.fn((a: number) => a);
    const memo = cached(fn as unknown as (...args: unknown[]) => unknown, { ttl: 100 });
    expect(memo(1)).toBe(1);
    vi.advanceTimersByTime(150);
    expect(memo(1)).toBe(1);
    expect(fn).toHaveBeenCalledTimes(2);
    vi.useRealTimers();
  });
});

describe('LRUCache', () => {
  it('set and get', () => {
    const lru = new LRUCache<string, number>(3);
    lru.set('a', 1);
    expect(lru.get('a')).toBe(1);
  });

  it('returns undefined for missing keys', () => {
    const lru = new LRUCache<string, number>(3);
    expect(lru.get('nope')).toBeUndefined();
  });

  it('evicts the least recently used entry when full', () => {
    const lru = new LRUCache<string, number>(2);
    lru.set('a', 1);
    lru.set('b', 2);
    lru.get('a'); // 'a' becomes most recently used
    lru.set('c', 3); // evicts 'b'
    expect(lru.get('a')).toBe(1);
    expect(lru.get('b')).toBeUndefined();
    expect(lru.get('c')).toBe(3);
  });

  it('delete removes a key', () => {
    const lru = new LRUCache<string, number>(2);
    lru.set('a', 1);
    expect(lru.delete('a')).toBe(true);
    expect(lru.get('a')).toBeUndefined();
  });

  it('clear empties the cache', () => {
    const lru = new LRUCache<string, number>(2);
    lru.set('a', 1);
    lru.set('b', 2);
    lru.clear();
    expect(lru.get('a')).toBeUndefined();
    expect(lru.get('b')).toBeUndefined();
  });

  it('has returns true for known keys and false for missing ones', () => {
    const lru = new LRUCache<string, number>(2);
    lru.set('a', 1);
    expect(lru.has('a')).toBe(true);
    expect(lru.has('b')).toBe(false);
  });

  it('size returns the number of entries', () => {
    const lru = new LRUCache<string, number>(3);
    lru.set('a', 1);
    lru.set('b', 2);
    expect(lru.size()).toBe(2);
  });
});

describe('sessionCache', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });

  it('sets and gets a value', () => {
    sessionCache.set('k', { name: 'X' });
    expect(sessionCache.get('k')).toEqual({ name: 'X' });
  });

  it('returns null for missing key', () => {
    expect(sessionCache.get('missing')).toBeNull();
  });

  it('expires after TTL', () => {
    vi.useFakeTimers();
    sessionCache.set('k', 'value', 100);
    expect(sessionCache.get('k')).toBe('value');
    vi.advanceTimersByTime(150);
    expect(sessionCache.get('k')).toBeNull();
    vi.useRealTimers();
  });

  it('has returns false for expired entries', () => {
    vi.useFakeTimers();
    sessionCache.set('k', 'value', 100);
    expect(sessionCache.has('k')).toBe(true);
    vi.advanceTimersByTime(150);
    expect(sessionCache.has('k')).toBe(false);
    vi.useRealTimers();
  });

  it('remove / delete clears an entry', () => {
    sessionCache.set('k', 'value');
    sessionCache.remove('k');
    expect(sessionCache.get('k')).toBeNull();
    sessionCache.set('k', 'value');
    sessionCache.delete('k');
    expect(sessionCache.get('k')).toBeNull();
  });

  it('clear removes everything', () => {
    sessionCache.set('a', 1);
    sessionCache.set('b', 2);
    sessionCache.clear();
    expect(sessionCache.get('a')).toBeNull();
    expect(sessionCache.get('b')).toBeNull();
  });

  it('returns null when stored value is malformed JSON', () => {
    window.sessionStorage.setItem('bad', '{not valid');
    expect(sessionCache.get('bad')).toBeNull();
  });

  it('size returns a number', () => {
    sessionCache.set('a', 1);
    sessionCache.set('b', 2);
    expect(typeof sessionCache.size()).toBe('number');
  });

  it('keys returns an array', () => {
    sessionCache.set('a', 1);
    sessionCache.set('b', 2);
    expect(Array.isArray(sessionCache.keys())).toBe(true);
  });
});
