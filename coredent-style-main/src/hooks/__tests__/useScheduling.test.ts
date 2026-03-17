import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useScheduling } from '@/hooks/useScheduling';
import { schedulingApi } from '@/services/schedulingApi';
import { addDays } from 'date-fns';
import type { Chair, AppointmentTypeConfig } from '@/types/clinic';

// Mock the scheduling API
vi.mock('@/services/schedulingApi', () => ({
  schedulingApi: {
    getAppointments: vi.fn(),
    getChairs: vi.fn(),
    getProviders: vi.fn(),
    getAppointmentTypes: vi.fn(),
  },
}));

describe('useScheduling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mock responses
    vi.mocked(schedulingApi.getAppointments).mockResolvedValue([]);
    vi.mocked(schedulingApi.getChairs).mockResolvedValue([
      { id: 'chair-1', name: 'Chair 1', isActive: true, color: '#3B82F6' } satisfies Chair,
    ]);
    vi.mocked(schedulingApi.getProviders).mockResolvedValue([
      { id: 'provider-1', name: 'Dr. Smith', color: '#10B981', isActive: true },
    ]);
    vi.mocked(schedulingApi.getAppointmentTypes).mockResolvedValue([
      { id: 'type-1', name: 'Cleaning', code: 'D1110', duration: 60, color: '#3b82f6', isActive: true, allowOnlineBooking: true } satisfies AppointmentTypeConfig,
    ]);
  });

  it('initializes with default values', () => {
    const { result } = renderHook(() => useScheduling());

    expect(result.current.view).toBe('day');
    expect(result.current.appointments).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.selectedAppointment).toBeNull();
  });

  it('loads data on mount', async () => {
    const { result } = renderHook(() => useScheduling());

    act(() => {
      result.current.loadData();
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(schedulingApi.getAppointments).toHaveBeenCalled();
    expect(schedulingApi.getChairs).toHaveBeenCalled();
    expect(schedulingApi.getProviders).toHaveBeenCalled();
    expect(schedulingApi.getAppointmentTypes).toHaveBeenCalled();
  });

  it('changes view correctly', () => {
    const { result } = renderHook(() => useScheduling());

    act(() => {
      result.current.setView('week');
    });

    expect(result.current.view).toBe('week');

    act(() => {
      result.current.setView('month');
    });

    expect(result.current.view).toBe('month');
  });

  it('navigates to today', () => {
    const { result } = renderHook(() => useScheduling());
    const today = new Date();

    act(() => {
      result.current.goToToday();
    });

    expect(result.current.currentDate.toDateString()).toBe(today.toDateString());
  });

  it('navigates to previous day', () => {
    const { result } = renderHook(() => useScheduling());
    const initialDate = result.current.currentDate;

    act(() => {
      result.current.goToPrevious();
    });

    const expectedDate = addDays(initialDate, -1);
    expect(result.current.currentDate.toDateString()).toBe(expectedDate.toDateString());
  });

  it('navigates to next day', () => {
    const { result } = renderHook(() => useScheduling());
    const initialDate = result.current.currentDate;

    act(() => {
      result.current.goToNext();
    });

    const expectedDate = addDays(initialDate, 1);
    expect(result.current.currentDate.toDateString()).toBe(expectedDate.toDateString());
  });

  it('adds appointment to local state', () => {
    const { result } = renderHook(() => useScheduling());
    const newAppointment = {
      id: 'apt-1',
      patientId: 'patient-1',
      patientName: 'John Doe',
      providerId: 'provider-1',
      providerName: 'Dr. Smith',
      chairId: 'chair-1',
      chairName: 'Chair 1',
      type: 'cleaning' as const,
      status: 'scheduled' as const,
      startTime: new Date(),
      endTime: new Date(),
      duration: 60,
      isConfirmed: false,
      reminderSent: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    act(() => {
      result.current.addAppointment(newAppointment);
    });

    expect(result.current.appointments).toHaveLength(1);
    expect(result.current.appointments[0]).toEqual(newAppointment);
  });

  it('updates appointment in local state', () => {
    const { result } = renderHook(() => useScheduling());
    const appointment = {
      id: 'apt-1',
      patientId: 'patient-1',
      patientName: 'John Doe',
      providerId: 'provider-1',
      providerName: 'Dr. Smith',
      chairId: 'chair-1',
      chairName: 'Chair 1',
      type: 'cleaning' as const,
      status: 'scheduled' as const,
      startTime: new Date(),
      endTime: new Date(),
      duration: 60,
      isConfirmed: false,
      reminderSent: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    act(() => {
      result.current.addAppointment(appointment);
    });

    act(() => {
      result.current.updateAppointment('apt-1', { status: 'confirmed' });
    });

    expect(result.current.appointments[0].status).toBe('confirmed');
  });

  it('removes appointment from local state', () => {
    const { result } = renderHook(() => useScheduling());
    const appointment = {
      id: 'apt-1',
      patientId: 'patient-1',
      patientName: 'John Doe',
      providerId: 'provider-1',
      providerName: 'Dr. Smith',
      chairId: 'chair-1',
      chairName: 'Chair 1',
      type: 'cleaning' as const,
      status: 'scheduled' as const,
      startTime: new Date(),
      endTime: new Date(),
      duration: 60,
      isConfirmed: false,
      reminderSent: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    act(() => {
      result.current.addAppointment(appointment);
    });

    expect(result.current.appointments).toHaveLength(1);

    act(() => {
      result.current.removeAppointment('apt-1');
    });

    expect(result.current.appointments).toHaveLength(0);
  });
});
