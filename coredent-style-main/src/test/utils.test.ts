import { describe, it, expect } from 'vitest';
import { toURLSearchParams, cn } from '@/lib/utils';

describe('toURLSearchParams', () => {
  it('should convert object to URLSearchParams', () => {
    const params = {
      foo: 'bar',
      baz: 123,
      qux: true,
    };
    const searchParams = toURLSearchParams(params);
    expect(searchParams.toString()).toBe('foo=bar&baz=123&qux=true');
  });

  it('should ignore null, undefined, and empty string', () => {
    const params = {
      foo: 'bar',
      baz: null,
      qux: undefined,
      quux: '',
    };
    const searchParams = toURLSearchParams(params);
    expect(searchParams.toString()).toBe('foo=bar');
  });

  it('should handle arrays', () => {
    const params = {
      ids: [1, 2, 3],
      tags: ['a', 'b'],
    };
    const searchParams = toURLSearchParams(params);
    expect(searchParams.get('ids')).toBe('1,2,3');
    expect(searchParams.get('tags')).toBe('a,b');
  });

  it('should handle empty arrays', () => {
    const params = {
      ids: [],
    };
    const searchParams = toURLSearchParams(params);
    expect(searchParams.has('ids')).toBe(false);
  });
});

describe('cn', () => {
  it('should merge classes', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
    expect(cn('foo', { bar: true, baz: false })).toBe('foo bar');
    expect(cn('p-4', 'p-2')).toBe('p-2'); // Tailwind merge
  });
});
