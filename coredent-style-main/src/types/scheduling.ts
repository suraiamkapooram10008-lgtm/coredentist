// ============================================
// CoreDent PMS - Scheduling Types
// Types for appointment scheduling module
// ============================================

import type { AppointmentStatus, AppointmentType } from './api';
import type { Chair, AppointmentTypeConfig } from './clinic';

// Extended appointment type for scheduling views
export interface ScheduleAppointment {
  id: string;
  patientId: string;
  patientName: string;
  patientPhone?: string;
  providerId: string;
  providerName: string;
  chairId: string;
  chairName: string;
  type: AppointmentType;
  typeConfig?: AppointmentTypeConfig;
  status: AppointmentStatus;
  startTime: Date;
  endTime: Date;
  duration: number; // in minutes
  notes?: string;
  isConfirmed: boolean;
  reminderSent: boolean;
  createdAt: string;
  updatedAt: string;
}

// Form data for creating/editing appointments
export interface AppointmentFormData {
  patientId: string;
  patientName: string;
  providerId: string;
  chairId: string;
  type: AppointmentType;
  date: Date;
  startTime: string; // HH:MM format
  duration: number;
  notes?: string;
}

// Provider/Dentist for scheduling
export interface ScheduleProvider {
  id: string;
  name: string;
  color: string;
  isActive: boolean;
}

// Calendar view types
export type CalendarView = 'day' | 'week' | 'month';

// Time slot for the schedule grid
export interface TimeSlot {
  time: string; // HH:MM format
  hour: number;
  minute: number;
  isHalfHour: boolean;
}

// Drag-and-drop event data
export interface DragData {
  appointmentId: string;
  originalChairId: string;
  originalStartTime: Date;
}

// Patient search result for quick search
export interface PatientSearchResult {
  id: string;
  name: string;
  phone: string;
  email: string;
  lastVisit?: string;
}

// Status configuration for display
export const appointmentStatusConfig: Record<AppointmentStatus, { label: string; color: string; bgClass: string }> = {
  scheduled: { label: 'Scheduled', color: '#6B7280', bgClass: 'bg-muted text-muted-foreground' },
  confirmed: { label: 'Confirmed', color: '#3B82F6', bgClass: 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200' },
  checked_in: { label: 'Checked In', color: '#10B981', bgClass: 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-200' },
  in_progress: { label: 'In Progress', color: '#F59E0B', bgClass: 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-200' },
  completed: { label: 'Completed', color: '#059669', bgClass: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200' },
  cancelled: { label: 'Cancelled', color: '#EF4444', bgClass: 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-200' },
  no_show: { label: 'No Show', color: '#DC2626', bgClass: 'bg-red-200 text-red-900 dark:bg-red-900/70 dark:text-red-100' },
};

// Generate time slots for the day view (30-minute intervals)
export function generateTimeSlots(startHour: number = 7, endHour: number = 19): TimeSlot[] {
  const slots: TimeSlot[] = [];
  for (let hour = startHour; hour <= endHour; hour++) {
    slots.push({ time: `${hour.toString().padStart(2, '0')}:00`, hour, minute: 0, isHalfHour: false });
    if (hour < endHour) {
      slots.push({ time: `${hour.toString().padStart(2, '0')}:30`, hour, minute: 30, isHalfHour: true });
    }
  }
  return slots;
}

// Calculate appointment position in the grid
export function calculateAppointmentPosition(
  startTime: Date,
  endTime: Date,
  dayStartHour: number = 7
): { top: number; height: number } {
  const startMinutes = startTime.getHours() * 60 + startTime.getMinutes();
  const endMinutes = endTime.getHours() * 60 + endTime.getMinutes();
  const dayStartMinutes = dayStartHour * 60;
  
  const pixelsPerMinute = 2; // 60px per 30 minutes = 2px per minute
  const top = (startMinutes - dayStartMinutes) * pixelsPerMinute;
  const height = Math.max((endMinutes - startMinutes) * pixelsPerMinute, 30); // minimum 30px height
  
  return { top, height };
}

// Format time for display
export function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
}

// Parse time string to hours and minutes
export function parseTimeString(timeStr: string): { hours: number; minutes: number } {
  const [hours, minutes] = timeStr.split(':').map(Number);
  return { hours, minutes };
}
