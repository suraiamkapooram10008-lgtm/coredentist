import { useState, useCallback } from 'react';
import { schedulingApi } from '@/services/schedulingApi';
import type { ScheduleAppointment, ScheduleProvider } from '@/types/scheduling';
import type { Chair, AppointmentTypeConfig } from '@/types/clinic';

export function useScheduling() {
  const [currentDate, setCurrentDate] = useState<Date>(() => new Date());
  const [view, setView] = useState<'day' | 'week' | 'month'>('day');
  const [appointments, setAppointments] = useState<ScheduleAppointment[]>([]);
  const [chairs, setChairs] = useState<Chair[]>([]);
  const [providers, setProviders] = useState<ScheduleProvider[]>([]);
  const [appointmentTypes, setAppointmentTypes] = useState<AppointmentTypeConfig[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedAppointment, setSelectedAppointment] = useState<ScheduleAppointment | null>(null);

  // Formatted date string
  const formattedDate = currentDate.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      // Calculate start and end date of range based on view
      const startDate = new Date(currentDate);
      const endDate = new Date(currentDate);

      if (view === 'day') {
        startDate.setHours(0, 0, 0, 0);
        endDate.setHours(23, 59, 59, 999);
      } else if (view === 'week') {
        const day = currentDate.getDay();
        startDate.setDate(currentDate.getDate() - day);
        startDate.setHours(0, 0, 0, 0);
        
        endDate.setDate(startDate.getDate() + 6);
        endDate.setHours(23, 59, 59, 999);
      } else { // month
        startDate.setDate(1);
        startDate.setHours(0, 0, 0, 0);
        
        endDate.setMonth(currentDate.getMonth() + 1);
        endDate.setDate(0);
        endDate.setHours(23, 59, 59, 999);
      }

      const [chairsData, providersData, typesData, appointmentsData] = await Promise.all([
        schedulingApi.getChairs(),
        schedulingApi.getProviders(),
        schedulingApi.getAppointmentTypes(),
        schedulingApi.getAppointments(startDate, endDate),
      ]);

      setChairs(chairsData);
      setProviders(providersData);
      setAppointmentTypes(typesData);
      
      const parsedAppointments = appointmentsData.map((appt) => ({
        ...appt,
        startTime: appt.startTime instanceof Date ? appt.startTime : new Date(appt.startTime),
        endTime: appt.endTime instanceof Date ? appt.endTime : new Date(appt.endTime),
        duration: typeof appt.duration === 'number' ? appt.duration : parseInt(appt.duration as any, 10) || 30
      }));
      setAppointments(parsedAppointments);
    } catch (error) {
      console.error('Failed to load scheduling data', error);
    } finally {
      setIsLoading(false);
    }
  }, [currentDate, view]);

  const goToToday = useCallback(() => {
    setCurrentDate(new Date());
  }, []);

  const goToPrevious = useCallback(() => {
    setCurrentDate((prev) => {
      const nextDate = new Date(prev);
      if (view === 'day') {
        nextDate.setDate(prev.getDate() - 1);
      } else if (view === 'week') {
        nextDate.setDate(prev.getDate() - 7);
      } else {
        nextDate.setMonth(prev.getMonth() - 1);
      }
      return nextDate;
    });
  }, [view]);

  const goToNext = useCallback(() => {
    setCurrentDate((prev) => {
      const nextDate = new Date(prev);
      if (view === 'day') {
        nextDate.setDate(prev.getDate() + 1);
      } else if (view === 'week') {
        nextDate.setDate(prev.getDate() + 7);
      } else {
        nextDate.setMonth(prev.getMonth() + 1);
      }
      return nextDate;
    });
  }, [view]);

  const goToDate = useCallback((date: Date) => {
    setCurrentDate(date);
  }, []);

  const addAppointment = useCallback((appointment: ScheduleAppointment) => {
    const parsed = {
      ...appointment,
      startTime: appointment.startTime instanceof Date ? appointment.startTime : new Date(appointment.startTime),
      endTime: appointment.endTime instanceof Date ? appointment.endTime : new Date(appointment.endTime),
      duration: typeof appointment.duration === 'number' ? appointment.duration : parseInt(appointment.duration as any, 10) || 30
    };
    setAppointments((prev) => [...prev, parsed]);
  }, []);

  const updateAppointment = useCallback((id: string, updates: Partial<ScheduleAppointment>) => {
    setAppointments((prev) =>
      prev.map((appt) => {
        if (appt.id !== id) return appt;
        const updated = { ...appt, ...updates };
        if (updates.startTime) {
          updated.startTime = updates.startTime instanceof Date ? updates.startTime : new Date(updates.startTime);
        }
        if (updates.endTime) {
          updated.endTime = updates.endTime instanceof Date ? updates.endTime : new Date(updates.endTime);
        }
        return updated;
      })
    );
    // If the selected appointment was updated, update its details too
    setSelectedAppointment((prev) => {
      if (prev?.id === id) {
        const updated = { ...prev, ...updates };
        if (updates.startTime) {
          updated.startTime = updates.startTime instanceof Date ? updates.startTime : new Date(updates.startTime);
        }
        if (updates.endTime) {
          updated.endTime = updates.endTime instanceof Date ? updates.endTime : new Date(updates.endTime);
        }
        return updated;
      }
      return prev;
    });
  }, []);

  const removeAppointment = useCallback((id: string) => {
    setAppointments((prev) => prev.filter((appt) => appt.id !== id));
    setSelectedAppointment((prev) => (prev?.id === id ? null : prev));
  }, []);

  return {
    currentDate,
    view,
    appointments,
    chairs,
    providers,
    appointmentTypes,
    isLoading,
    selectedAppointment,
    formattedDate,
    setView,
    setSelectedAppointment,
    goToToday,
    goToPrevious,
    goToNext,
    goToDate,
    loadData,
    addAppointment,
    updateAppointment,
    removeAppointment,
  };
}
