/**
 * AppointmentForm Component Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
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
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
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
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument();
    expect(screen.getByDisplayValue('9:00 AM')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Dr. Smith')).toBeInTheDocument();
  });

  it('should call onSubmit with form data', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <AppointmentForm
        appointmentTypes={mockAppointmentTypes}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
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
    const onCancel = vi.fn();

    render(
      <AppointmentForm
        appointmentTypes={mockAppointmentTypes}
        onSubmit={vi.fn()}
        onCancel={onCancel}
      />
    );

    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    await user.click(cancelButton);

    expect(onCancel).toHaveBeenCalled();
  });

  it('should display appointment types in select', () => {
    render(
      <AppointmentForm
        appointmentTypes={mockAppointmentTypes}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    // Check that appointment type options are available in the hidden select
    // The options are in a hidden select element for accessibility
    const hiddenSelect = document.querySelector('select[aria-hidden="true"]');
    expect(hiddenSelect).toBeInTheDocument();
    
    // Check options are present
    expect(hiddenSelect).toContainHTML('<option value="Checkup">Checkup (30 min)</option>');
    expect(hiddenSelect).toContainHTML('<option value="Cleaning">Cleaning (45 min)</option>');
    expect(hiddenSelect).toContainHTML('<option value="Root Canal">Root Canal (60 min)</option>');
  });

  it('should display status options', () => {
    render(
      <AppointmentForm
        appointmentTypes={mockAppointmentTypes}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    // There are two hidden select elements - one for appointment type and one for status
    // The second one is for status
    const hiddenSelects = document.querySelectorAll('select[aria-hidden="true"]');
    expect(hiddenSelects.length).toBe(2);
    
    const statusSelect = hiddenSelects[1];
    expect(statusSelect).toBeInTheDocument();
    
    // Check status options are present - using querySelector to find options
    const pendingOption = statusSelect.querySelector('option[value="Pending"]');
    const confirmedOption = statusSelect.querySelector('option[value="Confirmed"]');
    const completedOption = statusSelect.querySelector('option[value="Completed"]');
    const cancelledOption = statusSelect.querySelector('option[value="Cancelled"]');
    
    expect(pendingOption).toBeInTheDocument();
    expect(confirmedOption).toBeInTheDocument();
    expect(completedOption).toBeInTheDocument();
    expect(cancelledOption).toBeInTheDocument();
    
    // Check text content
    expect(pendingOption).toHaveTextContent('Pending');
    expect(confirmedOption).toHaveTextContent('Confirmed');
    expect(completedOption).toHaveTextContent('Completed');
    expect(cancelledOption).toHaveTextContent('Cancelled');
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
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /Update Appointment/i })).toBeInTheDocument();
  });

  it('should show Create button for new appointment', () => {
    render(
      <AppointmentForm
        appointmentTypes={mockAppointmentTypes}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /Create Appointment/i })).toBeInTheDocument();
  });

  it('should update form fields when user types', async () => {
    const user = userEvent.setup();

    render(
      <AppointmentForm
        appointmentTypes={mockAppointmentTypes}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
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
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByPlaceholderText('Enter patient name')).toBeInTheDocument();
  });
});
