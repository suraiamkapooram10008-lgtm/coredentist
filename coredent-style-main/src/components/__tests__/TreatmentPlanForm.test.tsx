/**
 * TreatmentPlanForm Component Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TreatmentPlanForm } from '../treatment/TreatmentPlanForm';
import type { TreatmentPlan } from '@/types/treatmentPlan';

describe('TreatmentPlanForm', () => {
  it('should render form with empty fields for new plan', () => {
    render(
      <TreatmentPlanForm
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByPlaceholderText('e.g., Comprehensive Restoration Plan')).toHaveValue('');
    expect(screen.getByPlaceholderText('Patient name')).toHaveValue('');
  });

  it('should populate form with plan data for editing', () => {
    const plan: TreatmentPlan = {
      id: '1',
      title: 'Root Canal Treatment',
      description: 'Complex root canal',
      patientId: 'p1',
      patientName: 'John Doe',
      notes: 'Follow up required',
    };

    render(
      <TreatmentPlanForm
        plan={plan}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByDisplayValue('Root Canal Treatment')).toBeInTheDocument();
    expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Complex root canal')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Follow up required')).toBeInTheDocument();
  });

  it('should call onSubmit with form data', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <TreatmentPlanForm
        patientId="test-patient-id"
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />
    );

    await user.type(
      screen.getByPlaceholderText('e.g., Comprehensive Restoration Plan'),
      'Root Canal'
    );
    await user.type(screen.getByPlaceholderText('Patient name'), 'Jane Doe');

    const submitButton = screen.getByRole('button', { name: /Create Plan/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalled();
    });
  });

  it('should call onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();

    render(
      <TreatmentPlanForm
        onSubmit={vi.fn()}
        onCancel={onCancel}
      />
    );

    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    await user.click(cancelButton);

    expect(onCancel).toHaveBeenCalled();
  });

  it('should show Save Changes button for existing plan', () => {
    const plan: TreatmentPlan = {
      id: '1',
      title: 'Root Canal',
      description: 'Treatment',
      patientId: 'p1',
      patientName: 'John Doe',
      notes: 'Notes',
    };

    render(
      <TreatmentPlanForm
        plan={plan}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /Save Changes/i })).toBeInTheDocument();
  });

  it('should show Create Plan button for new plan', () => {
    render(
      <TreatmentPlanForm
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /Create Plan/i })).toBeInTheDocument();
  });

  it('should display validation errors', async () => {
    const user = userEvent.setup();

    render(
      <TreatmentPlanForm
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    const submitButton = screen.getByRole('button', { name: /Create Plan/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Title is required/i)).toBeInTheDocument();
    });
  });

  it('should update form fields when user types', async () => {
    const user = userEvent.setup();

    render(
      <TreatmentPlanForm
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    const titleInput = screen.getByPlaceholderText('e.g., Comprehensive Restoration Plan');
    await user.type(titleInput, 'Root Canal');

    expect(titleInput).toHaveValue('Root Canal');
  });

  it('should handle optional fields', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <TreatmentPlanForm
        patientId="test-patient-id"
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />
    );

    await user.type(
      screen.getByPlaceholderText('e.g., Comprehensive Restoration Plan'),
      'Root Canal'
    );
    await user.type(screen.getByPlaceholderText('Patient name'), 'Jane Doe');

    const submitButton = screen.getByRole('button', { name: /Create Plan/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Root Canal',
          patientName: 'Jane Doe',
          patientId: 'test-patient-id',
        })
      );
    });
  });

  it('should reset form when plan prop changes', () => {
    const plan1: TreatmentPlan = {
      id: '1',
      title: 'Plan 1',
      description: 'Description 1',
      patientId: 'p1',
      patientName: 'John Doe',
      notes: 'Notes 1',
    };

    const plan2: TreatmentPlan = {
      id: '2',
      title: 'Plan 2',
      description: 'Description 2',
      patientId: 'p2',
      patientName: 'Jane Doe',
      notes: 'Notes 2',
    };

    const { rerender } = render(
      <TreatmentPlanForm
        plan={plan1}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByDisplayValue('Plan 1')).toBeInTheDocument();

    rerender(
      <TreatmentPlanForm
        plan={plan2}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByDisplayValue('Plan 2')).toBeInTheDocument();
  });
});
