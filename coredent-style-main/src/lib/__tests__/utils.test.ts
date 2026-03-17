import { describe, it, expect } from 'vitest';
import { cn, formatCurrency, formatDate, formatPhoneNumber } from '@/lib/utils';

describe('utils', () => {
  describe('cn', () => {
    it('merges class names', () => {
      expect(cn('foo', 'bar')).toBe('foo bar');
    });

    it('handles conditional classes', () => {
      expect(cn('foo', 'baz')).toBe('foo baz');
    });

    it('handles tailwind merge conflicts', () => {
      expect(cn('px-2', 'px-4')).toBe('px-4');
    });
  });

  describe('formatCurrency', () => {
    it('formats currency with default USD', () => {
      expect(formatCurrency(1234.56)).toBe('$1,234.56');
    });

    it('formats zero correctly', () => {
      expect(formatCurrency(0)).toBe('$0.00');
    });

    it('formats negative amounts', () => {
      expect(formatCurrency(-100)).toBe('-$100.00');
    });

    it('handles large numbers', () => {
      expect(formatCurrency(1000000)).toBe('$1,000,000.00');
    });
  });

  describe('formatDate', () => {
    it('formats date in default format', () => {
      const date = new Date('2024-02-15T10:30:00Z');
      expect(formatDate(date)).toMatch(/Feb(ruary)? 15, 2024/);
    });

    it('handles string dates', () => {
      expect(formatDate('2024-02-15')).toMatch(/Feb(ruary)? 15, 2024/);
    });

    it('formats with custom format', () => {
      const date = new Date('2024-02-15');
      expect(formatDate(date, 'yyyy-MM-dd')).toBe('2024-02-15');
    });
  });

  describe('formatPhoneNumber', () => {
    it('formats 10-digit phone number', () => {
      expect(formatPhoneNumber('5551234567')).toBe('(555) 123-4567');
    });

    it('handles already formatted numbers', () => {
      expect(formatPhoneNumber('(555) 123-4567')).toBe('(555) 123-4567');
    });

    it('handles numbers with country code', () => {
      expect(formatPhoneNumber('+15551234567')).toBe('+1 (555) 123-4567');
    });

    it('returns original if invalid format', () => {
      expect(formatPhoneNumber('123')).toBe('123');
    });
  });
});
