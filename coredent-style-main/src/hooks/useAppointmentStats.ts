/**
 * useAppointmentStats Hook
 * Fetches and manages appointment statistics
 */

import { useMemo } from 'react';
import type { Appointment } from '@/services/appointmentsApi';

interface AppointmentStatsResult {
  todayAppointments: number;
  confirmed: number;
  pending: number;
  cancelled: number;
  completed: number;
}

/**
 * Calculate appointment statistics from a list of appointments
 */
export function useAppointmentStats(appointments: Appointment[] = []): AppointmentStatsResult {
  return useMemo(() => {
    const stats: AppointmentStatsResult = {
      todayAppointments: appointments.length,
      confirmed: 0,
      pending: 0,
      cancelled: 0,
      completed: 0,
    };

    appointments.forEach((apt) => {
      switch (apt.status?.toLowerCase()) {
        case 'confirmed':
          stats.confirmed++;
          break;
        case 'pending':
          stats.pending++;
          break;
        case 'cancelled':
          stats.cancelled++;
          break;
        case 'completed':
          stats.completed++;
          break;
      }
    });

    return stats;
  }, [appointments]);
}
