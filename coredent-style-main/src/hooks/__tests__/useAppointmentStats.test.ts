/**
 * useAppointmentStats Hook Tests
 */

import { renderHook } from '@testing-library/react';
import { useAppointmentStats } from '../useAppointmentStats';
import type { Appointment } from '@/services/appointmentsApi';

describe('useAppointmentStats', () => {
  it('should calculate correct stats from appointments', () => {
    const appointments: Appointment[] = [
      { id: '1', patient: 'John', status: 'Confirmed', time: '9:00', type: 'Checkup', dentist: 'Dr. Smith', duration: '30' },
      { id: '2', patient: 'Jane', status: 'Pending', time: '10:00', type: 'Cleaning', dentist: 'Dr. Smith', duration: '45' },
      { id: '3', patient: 'Bob', status: 'Confirmed', time: '11:00', type: 'Checkup', dentist: 'Dr. Jones', duration: '30' },
      { id: '4', patient: 'Alice', status: 'Cancelled', time: '2:00', type: 'Root Canal', dentist: 'Dr. Smith', duration: '60' },
    ];

    const { result } = renderHook(() => useAppointmentStats(appointments));

    expect(result.current.todayAppointments).toBe(4);
    expect(result.current.confirmed).toBe(2);
    expect(result.current.pending).toBe(1);
    expect(result.current.cancelled).toBe(1);
    expect(result.current.completed).toBe(0);
  });

  it('should handle empty appointments array', () => {
    const { result } = renderHook(() => useAppointmentStats([]));

    expect(result.current.todayAppointments).toBe(0);
    expect(result.current.confirmed).toBe(0);
    expect(result.current.pending).toBe(0);
    expect(result.current.cancelled).toBe(0);
    expect(result.current.completed).toBe(0);
  });

  it('should handle undefined appointments', () => {
    const { result } = renderHook(() => useAppointmentStats(undefined));

    expect(result.current.todayAppointments).toBe(0);
    expect(result.current.confirmed).toBe(0);
    expect(result.current.pending).toBe(0);
    expect(result.current.cancelled).toBe(0);
    expect(result.current.completed).toBe(0);
  });

  it('should handle case-insensitive status matching', () => {
    const appointments: Appointment[] = [
      { id: '1', patient: 'John', status: 'CONFIRMED', time: '9:00', type: 'Checkup', dentist: 'Dr. Smith', duration: '30' },
      { id: '2', patient: 'Jane', status: 'pending', time: '10:00', type: 'Cleaning', dentist: 'Dr. Smith', duration: '45' },
    ];

    const { result } = renderHook(() => useAppointmentStats(appointments));

    expect(result.current.confirmed).toBe(1);
    expect(result.current.pending).toBe(1);
  });

  it('should update stats when appointments change', () => {
    const initialAppointments: Appointment[] = [
      { id: '1', patient: 'John', status: 'Confirmed', time: '9:00', type: 'Checkup', dentist: 'Dr. Smith', duration: '30' },
    ];

    const { result, rerender } = renderHook(
      ({ appointments }) => useAppointmentStats(appointments),
      { initialProps: { appointments: initialAppointments } }
    );

    expect(result.current.confirmed).toBe(1);

    const updatedAppointments: Appointment[] = [
      { id: '1', patient: 'John', status: 'Confirmed', time: '9:00', type: 'Checkup', dentist: 'Dr. Smith', duration: '30' },
      { id: '2', patient: 'Jane', status: 'Confirmed', time: '10:00', type: 'Cleaning', dentist: 'Dr. Smith', duration: '45' },
    ];

    rerender({ appointments: updatedAppointments });

    expect(result.current.confirmed).toBe(2);
    expect(result.current.todayAppointments).toBe(2);
  });
});
