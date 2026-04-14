/**
 * useTodayAppointments Hook
 * Fetches and manages today's appointments
 */

import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { appointmentsApi } from '@/services/api';
import type { Appointment } from '@/types/api';

interface UseTodayAppointmentsOptions {
  startDate?: Date;
  endDate?: Date;
  enabled?: boolean;
}

interface UseTodayAppointmentsResult {
  appointments: Appointment[];
  upcomingAppointments: Appointment[];
  upcomingCount: number;
  uniquePatientsCount: number;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}

/**
 * Hook to fetch and process today's appointments
 * 
 * @param options - Configuration options
 * @returns Appointments data and statistics
 * 
 * @example
 * const { appointments, upcomingCount } = useTodayAppointments({
 *   startDate: startOfToday,
 *   endDate: endOfToday
 * });
 */
export function useTodayAppointments(
  options: UseTodayAppointmentsOptions = {}
): UseTodayAppointmentsResult {
  const { startDate, endDate, enabled = true } = options;

  const { data: response, isLoading, isError, error } = useQuery({
    queryKey: ['dashboard', 'appointments', startDate?.toISOString(), endDate?.toISOString()],
    queryFn: () => appointmentsApi.list({
      startDate: startDate?.toISOString(),
      endDate: endDate?.toISOString(),
    }),
    staleTime: 2 * 60 * 1000, // 2 minutes
    enabled,
  });

  const appointments = useMemo(() => {
    return response?.success && response.data ? response.data : [];
  }, [response]);

  const upcomingAppointments = useMemo(() => {
    return [...appointments]
      .sort((a, b) => new Date(a.startTime).getTime() - new Date(b.startTime).getTime())
      .slice(0, 5);
  }, [appointments]);

  const upcomingCount = useMemo(() => {
    return upcomingAppointments.filter(
      apt => new Date(apt.startTime).getTime() > Date.now()
    ).length;
  }, [upcomingAppointments]);

  const uniquePatientsCount = useMemo(() => {
    return new Set(appointments.map(apt => apt.patientId)).size;
  }, [appointments]);

  return {
    appointments,
    upcomingAppointments,
    upcomingCount,
    uniquePatientsCount,
    isLoading,
    isError,
    error: error instanceof Error ? error : null,
  };
}
