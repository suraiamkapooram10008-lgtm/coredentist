// ============================================
// CoreDent PMS - Scheduling Hook
// State management for the scheduling module
// ============================================

import { useState, useCallback, useMemo } from 'react';
import { 
  addDays, 
  startOfWeek, 
  endOfWeek, 
  startOfMonth, 
  endOfMonth,
  isSameDay,
  format 
} from 'date-fns';
import type { CalendarView, ScheduleAppointment } from '@/types/scheduling';
import type { Chair, AppointmentTypeConfig } from '@/types/clinic';
import { schedulingApi } from '@/services/schedulingApi';
import type { ScheduleProvider } from '@/types/scheduling';

export function useScheduling() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<CalendarView>('day');
  const [appointments, setAppointments] = useState<ScheduleAppointment[]>([]);
  const [chairs, setChairs] = useState<Chair[]>([]);
  const [providers, setProviders] = useState<ScheduleProvider[]>([]);
  const [appointmentTypes, setAppointmentTypes] = useState<AppointmentTypeConfig[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState<ScheduleAppointment | null>(null);

  // Date range based on current view
  const dateRange = useMemo(() => {
    switch (view) {
      case 'day':
        return { start: currentDate, end: currentDate };
      case 'week':
        return { 
          start: startOfWeek(currentDate, { weekStartsOn: 0 }), 
          end: endOfWeek(currentDate, { weekStartsOn: 0 }) 
        };
      case 'month':
        return { 
          start: startOfMonth(currentDate), 
          end: endOfMonth(currentDate) 
        };
    }
  }, [currentDate, view]);

  // Load initial data
  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [appts, chairList, providerList, typeList] = await Promise.all([
        schedulingApi.getAppointments(dateRange.start, dateRange.end),
        schedulingApi.getChairs(),
        schedulingApi.getProviders(),
        schedulingApi.getAppointmentTypes(),
      ]);
      setAppointments(appts);
      setChairs(chairList);
      setProviders(providerList);
      setAppointmentTypes(typeList);
    } catch {
      // Failed to load scheduling data - will show empty state
    } finally {
      setIsLoading(false);
    }
  }, [dateRange]);

  // Navigation functions
  const goToToday = useCallback(() => setCurrentDate(new Date()), []);
  
  const goToPrevious = useCallback(() => {
    switch (view) {
      case 'day':
        setCurrentDate(d => addDays(d, -1));
        break;
      case 'week':
        setCurrentDate(d => addDays(d, -7));
        break;
      case 'month':
        setCurrentDate(d => new Date(d.getFullYear(), d.getMonth() - 1, 1));
        break;
    }
  }, [view]);

  const goToNext = useCallback(() => {
    switch (view) {
      case 'day':
        setCurrentDate(d => addDays(d, 1));
        break;
      case 'week':
        setCurrentDate(d => addDays(d, 7));
        break;
      case 'month':
        setCurrentDate(d => new Date(d.getFullYear(), d.getMonth() + 1, 1));
        break;
    }
  }, [view]);

  const goToDate = useCallback((date: Date) => setCurrentDate(date), []);

  // Get appointments for a specific day
  const getAppointmentsForDay = useCallback((date: Date) => {
    return appointments.filter(apt => isSameDay(apt.startTime, date));
  }, [appointments]);

  // Get appointments for a specific chair on a specific day
  const getAppointmentsForChair = useCallback((chairId: string, date: Date) => {
    return appointments.filter(
      apt => apt.chairId === chairId && isSameDay(apt.startTime, date)
    );
  }, [appointments]);

  // Add appointment to local state
  const addAppointment = useCallback((appointment: ScheduleAppointment) => {
    setAppointments(prev => [...prev, appointment]);
  }, []);

  // Update appointment in local state
  const updateAppointment = useCallback((id: string, updates: Partial<ScheduleAppointment>) => {
    setAppointments(prev => prev.map(apt => 
      apt.id === id ? { ...apt, ...updates } : apt
    ));
  }, []);

  // Remove appointment from local state
  const removeAppointment = useCallback((id: string) => {
    setAppointments(prev => prev.filter(apt => apt.id !== id));
  }, []);

  // Format date for display based on view
  const formattedDate = useMemo(() => {
    switch (view) {
      case 'day':
        return format(currentDate, 'EEEE, MMMM d, yyyy');
      case 'week': {
        const weekStart = startOfWeek(currentDate, { weekStartsOn: 0 });
        const weekEnd = endOfWeek(currentDate, { weekStartsOn: 0 });
        return `${format(weekStart, 'MMM d')} - ${format(weekEnd, 'MMM d, yyyy')}`;
      }
      case 'month':
        return format(currentDate, 'MMMM yyyy');
    }
  }, [currentDate, view]);

  return {
    // State
    currentDate,
    view,
    appointments,
    chairs,
    providers,
    appointmentTypes,
    isLoading,
    selectedAppointment,
    dateRange,
    formattedDate,

    // Setters
    setView,
    setSelectedAppointment,

    // Navigation
    goToToday,
    goToPrevious,
    goToNext,
    goToDate,

    // Data loading
    loadData,

    // Appointment queries
    getAppointmentsForDay,
    getAppointmentsForChair,

    // Appointment mutations (local state)
    addAppointment,
    updateAppointment,
    removeAppointment,
  };
}
