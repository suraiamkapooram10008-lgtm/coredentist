/**
 * Appointments Hooks
 * React Query hooks for appointment operations
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  listAppointments,
  getAppointment,
  createAppointment,
  updateAppointment,
  deleteAppointment,
  getAppointmentStats,
  listAppointmentTypes,
  sendAppointmentReminder,
  type AppointmentListParams,
  type Appointment,
} from '@/services/appointmentsApi';

/**
 * Hook to list appointments
 */
export const useAppointments = (params?: AppointmentListParams) => {
  return useQuery({
    queryKey: ['appointments', params],
    queryFn: () => listAppointments(params),
    staleTime: 30 * 1000, // 30 seconds
  });
};

/**
 * Hook to get a single appointment
 */
export const useAppointment = (id: string) => {
  return useQuery({
    queryKey: ['appointment', id],
    queryFn: () => getAppointment(id),
    enabled: !!id,
    staleTime: 30 * 1000,
  });
};

/**
 * Hook to get appointment statistics
 */
export const useAppointmentStats = () => {
  return useQuery({
    queryKey: ['appointmentStats'],
    queryFn: () => getAppointmentStats(),
    staleTime: 60 * 1000, // 1 minute
  });
};

/**
 * Hook to list appointment types
 */
export const useAppointmentTypes = () => {
  return useQuery({
    queryKey: ['appointmentTypes'],
    queryFn: () => listAppointmentTypes(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Hook to create an appointment
 */
export const useCreateAppointment = (options?: {
  onSuccess?: (data: Awaited<ReturnType<typeof createAppointment>>) => void;
  onError?: (error: Error) => void;
}) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Omit<Appointment, 'id'>) => createAppointment(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
      queryClient.invalidateQueries({ queryKey: ['appointmentStats'] });
      options?.onSuccess?.(data);
    },
    onError: options?.onError,
  });
};

/**
 * Hook to update an appointment
 */
export const useUpdateAppointment = (options?: {
  onSuccess?: (data: Awaited<ReturnType<typeof updateAppointment>>) => void;
  onError?: (error: Error) => void;
}) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Appointment> }) =>
      updateAppointment(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
      queryClient.invalidateQueries({ queryKey: ['appointmentStats'] });
      options?.onSuccess?.(data);
    },
    onError: options?.onError,
  });
};

/**
 * Hook to delete an appointment
 */
export const useDeleteAppointment = (options?: {
  onSuccess?: () => void;
  onError?: (error: Error) => void;
}) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteAppointment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
      queryClient.invalidateQueries({ queryKey: ['appointmentStats'] });
      options?.onSuccess?.();
    },
    onError: options?.onError,
  });
};

/**
 * Hook to send appointment reminder
 */
export const useSendAppointmentReminder = (options?: {
  onSuccess?: () => void;
  onError?: (error: Error) => void;
}) => {
  return useMutation({
    mutationFn: (id: string) => sendAppointmentReminder(id),
    onSuccess: options?.onSuccess,
    onError: options?.onError,
  });
};