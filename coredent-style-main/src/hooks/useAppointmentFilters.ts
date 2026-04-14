/**
 * useAppointmentFilters Hook
 * Manages appointment filtering and search logic
 */

import { useMemo } from 'react';
import type { Appointment } from '@/services/appointmentsApi';

interface FilterOptions {
  searchTerm?: string;
  status?: string;
  dentist?: string;
}

/**
 * Filter appointments based on search and status criteria
 */
export function useAppointmentFilters(
  appointments: Appointment[] = [],
  filters: FilterOptions = {}
): Appointment[] {
  return useMemo(() => {
    let filtered = [...appointments];

    // Search by patient name or type
    if (filters.searchTerm) {
      const term = filters.searchTerm.toLowerCase();
      filtered = filtered.filter(
        (apt) =>
          apt.patient?.toLowerCase().includes(term) ||
          apt.patientName?.toLowerCase().includes(term) ||
          apt.type?.toLowerCase().includes(term)
      );
    }

    // Filter by status
    if (filters.status) {
      filtered = filtered.filter((apt) => apt.status === filters.status);
    }

    // Filter by dentist
    if (filters.dentist) {
      filtered = filtered.filter((apt) => apt.dentist === filters.dentist);
    }

    return filtered;
  }, [appointments, filters]);
}

/**
 * Get unique dentists from appointments
 */
export function useUniqueDentists(appointments: Appointment[] = []): string[] {
  return useMemo(() => {
    const dentists = new Set<string>();
    appointments.forEach((apt) => {
      if (apt.dentist) {
        dentists.add(apt.dentist);
      }
    });
    return Array.from(dentists).sort();
  }, [appointments]);
}

/**
 * Get status color for badge display
 */
export function getStatusColor(status: string): string {
  switch (status?.toLowerCase()) {
    case 'confirmed':
      return 'bg-green-500';
    case 'pending':
      return 'bg-yellow-500';
    case 'cancelled':
      return 'bg-red-500';
    case 'completed':
      return 'bg-blue-500';
    default:
      return 'bg-gray-500';
  }
}
