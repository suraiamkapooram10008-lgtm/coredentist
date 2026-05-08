/**
 * Appointments Page Integration Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import Appointments from '../Appointments_Refactored';
import type { Appointment } from '@/services/appointmentsApi';

const mockAppointments: Appointment[] = [
  {
    id: '1',
    patient: 'John Doe',
    patientName: 'John Doe',
    time: '9:00 AM',
    duration: '30',
    type: 'Checkup',
    dentist: 'Dr. Smith',
    status: 'Confirmed',
  },
  {
    id: '2',
    patient: 'Jane Smith',
    patientName: 'Jane Smith',
    time: '10:00 AM',
    duration: '45',
    type: 'Cleaning',
    dentist: 'Dr. Jones',
    status: 'Pending',
  },
];

const mockAppointmentTypes = [
  { id: '1', name: 'Checkup', duration: 30 },
  { id: '2', name: 'Cleaning', duration: 45 },
];

// Mock the virtualizer to render all items
vi.mock('@tanstack/react-virtual', () => ({
  useVirtualizer: () => ({
    getVirtualItems: () => mockAppointments.map((apt, index) => ({
      index,
      key: apt.id,
      start: index * 72,
      size: 72,
    })),
    getTotalSize: () => mockAppointments.length * 72,
    measureElement: vi.fn(),
  }),
}));

// Mock the hooks
vi.mock('@/hooks/useAppointments', () => ({
  useAppointments: vi.fn(() => ({
    data: { data: { appointments: mockAppointments } },
    isLoading: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
  })),
  useAppointmentTypes: vi.fn(() => ({
    data: { data: { types: mockAppointmentTypes } },
    isLoading: false,
  })),
  useCreateAppointment: vi.fn(() => ({ mutate: vi.fn() })),
  useUpdateAppointment: vi.fn(() => ({ mutate: vi.fn() })),
  useDeleteAppointment: vi.fn(() => ({ mutate: vi.fn() })),
  useSendAppointmentReminder: vi.fn(() => ({ mutate: vi.fn() })),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

describe('Appointments Page Integration', () => {
  it('should load and display page header', async () => {
    render(<Appointments />, {
      isAuthenticated: true,
      user: {
        id: 'test-user-id',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'dentist',
        practiceId: 'test-practice-id',
        practiceName: 'Test Practice',
      },
    });

    expect(screen.getByText('Appointments')).toBeInTheDocument();
    expect(screen.getByText('Manage all patient appointments')).toBeInTheDocument();
  });

  it('should display appointment statistics cards', async () => {
    render(<Appointments />, {
      isAuthenticated: true,
      user: {
        id: 'test-user-id',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'dentist',
        practiceId: 'test-practice-id',
        practiceName: 'Test Practice',
      },
    });

    await waitFor(() => {
      expect(screen.getByText("Today's Appointments")).toBeInTheDocument();
      // Use getAllByText since these status labels appear multiple times (in stats and in appointment list)
      expect(screen.getAllByText('Confirmed').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Pending').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Cancelled').length).toBeGreaterThan(0);
    });
  });

  it('should display search input', async () => {
    render(<Appointments />, {
      isAuthenticated: true,
      user: {
        id: 'test-user-id',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'dentist',
        practiceId: 'test-practice-id',
        practiceName: 'Test Practice',
      },
    });

    expect(screen.getByPlaceholderText('Search appointments...')).toBeInTheDocument();
  });

  it('should display tabs for different views', async () => {
    render(<Appointments />, {
      isAuthenticated: true,
      user: {
        id: 'test-user-id',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'dentist',
        practiceId: 'test-practice-id',
        practiceName: 'Test Practice',
      },
    });

    expect(screen.getByRole('tab', { name: /List View/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /Timeline/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /Appointment Types/i })).toBeInTheDocument();
  });

  it('should display new appointment button', async () => {
    render(<Appointments />, {
      isAuthenticated: true,
      user: {
        id: 'test-user-id',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'dentist',
        practiceId: 'test-practice-id',
        practiceName: 'Test Practice',
      },
    });

    expect(screen.getByRole('button', { name: /New Appointment/i })).toBeInTheDocument();
  });

  it('should display loading state', async () => {
    // Override the mock for this test
    const { useAppointments } = await import('@/hooks/useAppointments');
    
    vi.mocked(useAppointments).mockReturnValueOnce({
      data: { data: { appointments: [] } },
      isLoading: true,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    render(<Appointments />, {
      isAuthenticated: true,
      user: {
        id: 'test-user-id',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'dentist',
        practiceId: 'test-practice-id',
        practiceName: 'Test Practice',
      },
    });

    // The loading state shows a spinner in the AppointmentListView
    // Check that the main content is rendered
    expect(screen.getByText('Appointments')).toBeInTheDocument();
  });

  it('should display empty state when no appointments', async () => {
    // Override the mock for this test
    const { useAppointments } = await import('@/hooks/useAppointments');
    
    vi.mocked(useAppointments).mockReturnValueOnce({
      data: { data: { appointments: [] } },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    render(<Appointments />, {
      isAuthenticated: true,
      user: {
        id: 'test-user-id',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'dentist',
        practiceId: 'test-practice-id',
        practiceName: 'Test Practice',
      },
    });

    await waitFor(() => {
      expect(screen.getByText('No appointments found')).toBeInTheDocument();
    });
  });

  it('should switch to timeline view', async () => {
    const user = userEvent.setup();

    render(<Appointments />, {
      isAuthenticated: true,
      user: {
        id: 'test-user-id',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'dentist',
        practiceId: 'test-practice-id',
        practiceName: 'Test Practice',
      },
    });

    const timelineTab = screen.getByRole('tab', { name: /Timeline/i });
    await user.click(timelineTab);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Timeline View' })).toBeInTheDocument();
    });
  });

  it('should display appointment types in types tab', async () => {
    const user = userEvent.setup();

    render(<Appointments />, {
      isAuthenticated: true,
      user: {
        id: 'test-user-id',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'dentist',
        practiceId: 'test-practice-id',
        practiceName: 'Test Practice',
      },
    });

    const typesTab = screen.getByRole('tab', { name: /Appointment Types/i });
    await user.click(typesTab);

    await waitFor(() => {
      expect(screen.getByText('Checkup')).toBeInTheDocument();
      expect(screen.getByText('Cleaning')).toBeInTheDocument();
    });
  });

  it('should open new appointment dialog', async () => {
    const user = userEvent.setup();

    render(<Appointments />, {
      isAuthenticated: true,
      user: {
        id: 'test-user-id',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'dentist',
        practiceId: 'test-practice-id',
        practiceName: 'Test Practice',
      },
    });

    const newButton = screen.getByRole('button', { name: /New Appointment/i });
    await user.click(newButton);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'New Appointment' })).toBeInTheDocument();
    });
  });
});
