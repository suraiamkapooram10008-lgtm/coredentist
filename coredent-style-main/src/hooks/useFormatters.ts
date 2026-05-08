/**
 * useFormatters Hook
 * Provides formatting utilities for common data types
 */

import { useCallback } from 'react';

interface UseFormattersResult {
  formatCurrency: (amount: number) => string;
  formatAppointmentType: (type: string) => string;
  formatDate: (date: Date | string) => string;
  formatTime: (date: Date | string) => string;
}

/**
 * Hook to get formatting utilities
 * 
 * @returns Object with formatting functions
 * 
 * @example
 * const { formatCurrency, formatAppointmentType } = useFormatters();
 * const price = formatCurrency(100);
 * const type = formatAppointmentType('root_canal');
 */
export function useFormatters(): UseFormattersResult {
  const formatCurrency = useCallback((amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(amount);
  }, []);

  const formatAppointmentType = useCallback((value: string): string => {
    if (!value) return '';
    return value
      .split('_')
      .map(word => (word?.charAt(0) || '?').toUpperCase() + (word?.slice(1) || ''))
      .join(' ');
  }, []);

  const formatDate = useCallback((date: Date | string): string => {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return dateObj.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }, []);

  const formatTime = useCallback((date: Date | string): string => {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return dateObj.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  }, []);

  return {
    formatCurrency,
    formatAppointmentType,
    formatDate,
    formatTime,
  };
}
