import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';
import Appointments from '../Appointments';
import { server } from '@/test/mocks/server';
import { http, HttpResponse } from 'msw';

// Mock components that might not be fully implemented
vi.mock('@/components/appointments/AppointmentCalendar', () => ({
  default: ({ appointments, onAppointmentClick }: any) => (
    <div data-testid="appointment-calendar">
      <div>Calendar View</div>
      {appointments?.map((apt: any) => (
        <div
          key={apt.id}
          data-testid={`appointment-${apt.id}`}
          onClick={() => onAppointmentClick?.(apt)}
          style={{ cursor: 'pointer' }}
        >
          {apt.patientName} - {apt.time}
        </div>
      ))}
    </div>
  ),
}));

vi.mock('@/components/appointments/AppointmentForm', () => ({
  default: ({ onSubmit, onCancel, appointment }: any) => (
    <div data-testid="appointment-form">
      <h3>{appointment ? 'Edit Appointment' : 'New Appointment'}</h3>
      <button onClick={() => onSubmit?.({ patientName: 'Test Patient', time: '10:00 AM' })}>
        Save
      </button>
      <button onClick={onCancel}>Cancel</button>
    </div>
  ),
}));

// Mock hooks
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          {children}
        </AuthProvider>
      </QueryClientProvider>
    </BrowserRouter>
  );
};

describe('Appointments Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubEnv('MODE', 'test');
    vi.stubEnv('VITE_DEV_BYPASS_AUTH', 'true'); // Enable dev bypass for easier testing
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  const mockAppointments = [
    {
      id: 'apt-1',
      patientId: 'patient-1',
      patientName: 'John Doe',
      practitionerId: 'doc-1',
      practitionerName: 'Dr. Smith',
      startTime: '2024-03-16T10:00:00Z',
      endTime: '2024-03-16T11:00:00Z',
      status: 'scheduled',
      type: 'checkup',
      notes: 'Regular checkup',
      time: '10:00 AM',
    },
    {
      id: 'apt-2',
      patientId: 'patient-2',
      patientName: 'Jane Smith',
      practitionerId: 'doc-1',
      practitionerName: 'Dr. Smith',
      startTime: '2024-03-16T14:00:00Z',
      endTime: '2024-03-16T15:00:00Z',
      status: 'scheduled',
      type: 'cleaning',
      notes: 'Dental cleaning',
      time: '2:00 PM',
    },
  ];

  it('should render appointments page with calendar', async () => {
    server.use(
      http.get('/api/v1/appointments', () => {
        return HttpResponse.json(mockAppointments);
      })
    );

    render(
      <TestWrapper>
        <Appointments />
      </TestWrapper>
    );

    // Should show loading initially
    expect(screen.getByText(/loading/i)).toBeInTheDocument();

    // Should show calendar after loading
    await waitFor(() => {
      expect(screen.getByTestId('appointment-calendar')).toBeInTheDocument();
    });

    expect(screen.getByText('Calendar View')).toBeInTheDocument();
  });

  it('should display appointments in calendar', async () => {
    server.use(
      http.get('/api/v1/appointments', () => {
        return HttpResponse.json(mockAppointments);
      })
    );

    render(
      <TestWrapper>
        <Appointments />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('appointment-apt-1')).toBeInTheDocument();
      expect(screen.getByTestId('appointment-apt-2')).toBeInTheDocument();
    });

    expect(screen.getByText('John Doe - 10:00 AM')).toBeInTheDocument();
    expect(screen.getByText('Jane Smith - 2:00 PM')).toBeInTheDocument();
  });

  it('should handle appointment click', async () => {
    const user = userEvent.setup();

    server.use(
      http.get('/api/v1/appointments', () => {
        return HttpResponse.json(mockAppointments);
      })
    );

    render(
      <TestWrapper>
        <Appointments />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('appointment-apt-1')).toBeInTheDocument();
    });

    // Click on appointment
    await user.click(screen.getByTestId('appointment-apt-1'));

    // Should show appointment details or form
    await waitFor(() => {
      expect(screen.getByText('Edit Appointment')).toBeInTheDocument();
    });
  });

  it('should handle new appointment creation', async () => {
    const user = userEvent.setup();

    server.use(
      http.get('/api/v1/appointments', () => {
        return HttpResponse.json(mockAppointments);
      }),
      http.post('/api/v1/appointments', async ({ request }) => {
        const body = await request.json() as any;
        return HttpResponse.json({
          id: 'apt-3',
          ...body,
          createdAt: '2024-03-16T00:00:00Z',
          updatedAt: '2024-03-16T00:00:00Z',
        }, { status: 201 });
      })
    );

    render(
      <TestWrapper>
        <Appointments />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('appointment-calendar')).toBeInTheDocument();
    });

    // Look for new appointment button (might be in header or floating action button)
    const newButton = screen.getByRole('button', { name: /new|add|create/i });
    await user.click(newButton);

    // Should show appointment form
    await waitFor(() => {
      expect(screen.getByText('New Appointment')).toBeInTheDocument();
    });

    // Fill and submit form
    await user.click(screen.getByText('Save'));

    // Should close form and refresh appointments
    await waitFor(() => {
      expect(screen.queryByText('New Appointment')).not.toBeInTheDocument();
    });
  });

  it('should handle appointment update', async () => {
    const user = userEvent.setup();

    server.use(
      http.get('/api/v1/appointments', () => {
        return HttpResponse.json(mockAppointments);
      }),
      http.put('/api/v1/appointments/apt-1', async ({ request }) => {
        const body = await request.json() as any;
        return HttpResponse.json({
          ...mockAppointments[0],
          ...body,
          updatedAt: '2024-03-16T12:00:00Z',
        });
      })
    );

    render(
      <TestWrapper>
        <Appointments />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('appointment-apt-1')).toBeInTheDocument();
    });

    // Click on appointment to edit
    await user.click(screen.getByTestId('appointment-apt-1'));

    await waitFor(() => {
      expect(screen.getByText('Edit Appointment')).toBeInTheDocument();
    });

    // Save changes
    await user.click(screen.getByText('Save'));

    // Should close form
    await waitFor(() => {
      expect(screen.queryByText('Edit Appointment')).not.toBeInTheDocument();
    });
  });

  it('should handle appointment deletion', async () => {
    const user = userEvent.setup();

    server.use(
      http.get('/api/v1/appointments', () => {
        return HttpResponse.json(mockAppointments);
      }),
      http.delete('/api/v1/appointments/apt-1', () => {
        return HttpResponse.json({ message: 'Appointment deleted successfully' });
      })
    );

    render(
      <TestWrapper>
        <Appointments />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('appointment-apt-1')).toBeInTheDocument();
    });

    // Right-click or find delete button (implementation dependent)
    // This would depend on how delete is implemented in the actual component
    const deleteButton = screen.getByRole('button', { name: /delete|remove/i });
    await user.click(deleteButton);

    // Confirm deletion if there's a confirmation dialog
    const confirmButton = screen.getByRole('button', { name: /confirm|yes|delete/i });
    await user.click(confirmButton);

    // Appointment should be removed
    await waitFor(() => {
      expect(screen.queryByTestId('appointment-apt-1')).not.toBeInTheDocument();
    });
  });

  it('should handle API errors gracefully', async () => {
    server.use(
      http.get('/api/v1/appointments', () => {
        return HttpResponse.json(
          { message: 'Failed to fetch appointments' },
          { status: 500 }
        );
      })
    );

    render(
      <TestWrapper>
        <Appointments />
      </TestWrapper>
    );

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
    });
  });

  it('should filter appointments by date range', async () => {
    const user = userEvent.setup();

    server.use(
      http.get('/api/v1/appointments', ({ request }) => {
        const url = new URL(request.url);
        const startDate = url.searchParams.get('startDate');
        const endDate = url.searchParams.get('endDate');
        
        // Return filtered appointments based on date range
        if (startDate && endDate) {
          return HttpResponse.json([mockAppointments[0]]); // Only first appointment
        }
        
        return HttpResponse.json(mockAppointments);
      })
    );

    render(
      <TestWrapper>
        <Appointments />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('appointment-calendar')).toBeInTheDocument();
    });

    // Should show both appointments initially
    expect(screen.getByTestId('appointment-apt-1')).toBeInTheDocument();
    expect(screen.getByTestId('appointment-apt-2')).toBeInTheDocument();

    // Apply date filter (implementation dependent)
    const dateFilter = screen.getByRole('button', { name: /filter|date/i });
    await user.click(dateFilter);

    // After filtering, should show fewer appointments
    await waitFor(() => {
      expect(screen.getByTestId('appointment-apt-1')).toBeInTheDocument();
      expect(screen.queryByTestId('appointment-apt-2')).not.toBeInTheDocument();
    });
  });

  it('should handle empty appointments list', async () => {
    server.use(
      http.get('/api/v1/appointments', () => {
        return HttpResponse.json([]);
      })
    );

    render(
      <TestWrapper>
        <Appointments />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/no appointments|empty/i)).toBeInTheDocument();
    });
  });
});