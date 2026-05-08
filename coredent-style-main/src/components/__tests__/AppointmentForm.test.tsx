/**
 * AppointmentForm Component Tests
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AppointmentForm } from '../appointments/AppointmentForm';
import type { Appointment } from '@/services/appointmentsApi';

describe('AppointmentForm', () => {
  const mockAppointmentTypes = [
    { id: '1', name: 'Checkup', duration: 30 },
    { id: '2', name: 'Cleaning', duration: 45 },
    { id: '3', name: 'Root Canal', duration: 60 },
  ];

  it('should render form with empty fields for new appointment', () => {
    render(
      <AppointmentForm
        appointmentTypes={mockAppointmentTypes}
        onSubmit={jest.fn()}
        onCancel={jest.fn()}
      />
    );

    expect(screen.getByPlaceholderText('Enter patient name')).toHaveValue('');
    expect(screen.getByPlaceholderText('e.g., 9:00 AM')).toHaveValue('');
  });

  it('should populate form with appointment data for editing', () => {
    const appointment: Appointment = {
      id: '1',
      patient: 'John Doe',
      patientName: 'John Doe',
      time: '9:00 AM',
      duration: '30',
      type: 'Checkup',
      dentist: 'Dr. Smith',
      status: 'Confirmed',
    };

    render(
      <AppointmentForm
        appointment={appointment}
        appointmentTypes={mockAppointmentTypes}
        onSubmit={jest.fn()}
        onCancel={jest.fn()}
      />
    );

    expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument();
    expect(screen.getByDisplayValue('9:00 AM')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Dr. Smith')).toBeInTheDocument();
  });

  it('should call onSubmit with form data', async () => {
    const user = userEvent.setup();
    const onSubmit = jest.fn();

    render(
      <AppointmentForm
        appointmentTypes={mockAppointmentTypes}
        onSubmit={onSubmit}
        onCancel={jest.fn()}
      />
    );

    await user.type(screen.getByPlaceholderText('Enter patient name'), 'Jane Doe');
    await user.type(screen.getByPlaceholderText('e.g., 9:00 AM'), '10:00 AM');
    await user.type(screen.getByPlaceholderText('e.g., Dr. Wilson'), 'Dr. Jones');

    const submitButton = screen.getByRole('button', { name: /Create Appointment/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalled();
    });
  });

  it('should call onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup();
    const onCancel = jest.fn();

    render(
      <AppointmentForm
        appointmentTypes={mockAppointmentTypes}
        onSubmit={jest.fn()}
        onCancel={onCancel}
      />
    );

    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    await user.click(cancelButton);

    expect(onCancel).toHaveBeenCalled();
  });

  it('should display appointment types in select', async () => {
    const user = userEvent.setup();

    render(
      <AppointmentForm
        appointmentTypes={mockAppointmentTypes}
        onSubmit={jest.fn()}
        onCancel={jest.fn()}
      />
    );

    const typeSelect = screen.getByDisplayValue('Select type');
    await user.click(typeSelect);

    expect(screen.getByText('Checkup (30 min)')).toBeInTheDocument();
    expect(screen.getByText('Cleaning (45 min)')).toBeInTheDocument();
    expect(screen.getByText('Root Canal (60 min)')).toBeInTheDocument();
  });

  it('should display status options', async () => {
    const user = userEvent.setup();

    render(
      <AppointmentForm
        appointmentTypes={mockAppointmentTypes}
        onSubmit={jest.fn()}
        onCancel={jest.fn()}
      />
    );

    const statusSelect = screen.getByDisplayValue('Pending');
    await user.click(statusSelect);

    expect(screen.getByText('Pending')).toBeInTheDocument();
    expect(screen.getByText('Confirmed')).toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('Cancelled')).toBeInTheDocument();
  });

  it('should show Update button for existing appointment', () => {
    const appointment: Appointment = {
      id: '1',
      patient: 'John Doe',
      patientName: 'John Doe',
      time: '9:00 AM',
      duration: '30',
      type: 'Checkup',
      dentist: 'Dr. Smith',
      status: 'Confirmed',
    };

    render(
      <AppointmentForm
        appointment={appointment}
        appointmentTypes={mockAppointmentTypes}
        onSubmit={jest.fn()}
        onCancel={jest.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /Update Appointment/i })).toBeInTheDocument();
  });

  it('should show Create button for new appointment', () => {
    render(
      <AppointmentForm
        appointmentTypes={mockAppointmentTypes}
        onSubmit={jest.fn()}
        onCancel={jest.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /Create Appointment/i })).toBeInTheDocument();
  });

  it('should update form fields when user types', async () => {
    const user = userEvent.setup();

    render(
      <AppointmentForm
        appointmentTypes={mockAppointmentTypes}
        onSubmit={jest.fn()}
        onCancel={jest.fn()}
      />
    );

    const patientInput = screen.getByPlaceholderText('Enter patient name');
    await user.type(patientInput, 'Jane Doe');

    expect(patientInput).toHaveValue('Jane Doe');
  });

  it('should handle empty appointment types', () => {
    render(
      <AppointmentForm
        appointmentTypes={[]}
        onSubmit={jest.fn()}
        onCancel={jest.fn()}
      />
    );

    expect(screen.getByPlaceholderText('Enter patient name')).toBeInTheDocument();
  });
});
