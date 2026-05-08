/**
 * useTreatmentPlanForm Hook Tests
 */

import { renderHook, act } from '@testing-library/react';
import { useTreatmentPlanForm } from '../useTreatmentPlanForm';
import type { TreatmentPlan } from '@/types/treatmentPlan';

describe('useTreatmentPlanForm', () => {
  it('should initialize with empty form data', () => {
    const { result } = renderHook(() => useTreatmentPlanForm());

    expect(result.current.formData.title).toBe('');
    expect(result.current.formData.description).toBe('');
    expect(result.current.formData.patientName).toBe('');
    expect(result.current.formData.notes).toBe('');
    expect(result.current.errors).toEqual({});
  });

  it('should initialize with plan data', () => {
    const plan: TreatmentPlan = {
      id: '1',
      title: 'Root Canal',
      description: 'Complex root canal treatment',
      patientId: 'p1',
      patientName: 'John Doe',
      notes: 'Follow up after 2 weeks',
    };

    const { result } = renderHook(() => useTreatmentPlanForm(plan));

    expect(result.current.formData.title).toBe('Root Canal');
    expect(result.current.formData.description).toBe('Complex root canal treatment');
    expect(result.current.formData.patientName).toBe('John Doe');
    expect(result.current.formData.notes).toBe('Follow up after 2 weeks');
  });

  it('should update field value', () => {
    const { result } = renderHook(() => useTreatmentPlanForm());

    act(() => {
      result.current.updateField('title', 'New Title');
    });

    expect(result.current.formData.title).toBe('New Title');
  });

  it('should clear error when field is updated', () => {
    const { result } = renderHook(() => useTreatmentPlanForm());

    act(() => {
      result.current.validate();
    });

    expect(result.current.errors.title).toBeDefined();

    act(() => {
      result.current.updateField('title', 'Valid Title');
    });

    expect(result.current.errors.title).toBeUndefined();
  });

  it('should validate required fields', () => {
    const { result } = renderHook(() => useTreatmentPlanForm());

    act(() => {
      const isValid = result.current.validate();
      expect(isValid).toBe(false);
    });

    expect(result.current.errors.title).toBeDefined();
    expect(result.current.errors.patientName).toBeDefined();
  });

  it('should validate title length', () => {
    const { result } = renderHook(() => useTreatmentPlanForm());

    // Update fields first
    act(() => {
      result.current.updateField('title', 'a'.repeat(101));
      result.current.updateField('patientName', 'John Doe');
    });

    // Then validate (state is now updated)
    act(() => {
      const isValid = result.current.validate();
      expect(isValid).toBe(false);
    });

    expect(result.current.errors.title).toBeDefined();
  });

  it('should validate description length', () => {
    const { result } = renderHook(() => useTreatmentPlanForm());

    // Update fields first
    act(() => {
      result.current.updateField('title', 'Valid Title');
      result.current.updateField('patientName', 'John Doe');
      result.current.updateField('description', 'a'.repeat(501));
    });

    // Then validate
    act(() => {
      const isValid = result.current.validate();
      expect(isValid).toBe(false);
    });

    expect(result.current.errors.description).toBeDefined();
  });

  it('should validate notes length', () => {
    const { result } = renderHook(() => useTreatmentPlanForm());

    // Update fields first
    act(() => {
      result.current.updateField('title', 'Valid Title');
      result.current.updateField('patientName', 'John Doe');
      result.current.updateField('notes', 'a'.repeat(1001));
    });

    // Then validate
    act(() => {
      const isValid = result.current.validate();
      expect(isValid).toBe(false);
    });

    expect(result.current.errors.notes).toBeDefined();
  });

  it('should pass validation with valid data', () => {
    const { result } = renderHook(() => useTreatmentPlanForm());

    // Update fields first
    act(() => {
      result.current.updateField('title', 'Root Canal');
      result.current.updateField('patientName', 'John Doe');
      result.current.updateField('description', 'Complex treatment');
      result.current.updateField('notes', 'Follow up required');
    });

    // Then validate
    act(() => {
      const isValid = result.current.validate();
      expect(isValid).toBe(true);
    });

    expect(Object.keys(result.current.errors)).toHaveLength(0);
  });

  it('should reset form data', () => {
    const { result } = renderHook(() => useTreatmentPlanForm());

    act(() => {
      result.current.updateField('title', 'Root Canal');
      result.current.updateField('patientName', 'John Doe');
    });

    act(() => {
      result.current.reset();
    });

    expect(result.current.formData.title).toBe('');
    expect(result.current.formData.patientName).toBe('');
    expect(result.current.errors).toEqual({});
  });

  it('should handle plan updates', () => {
    const initialPlan: TreatmentPlan = {
      id: '1',
      title: 'Initial Title',
      description: 'Initial description',
      patientId: 'p1',
      patientName: 'John Doe',
      notes: 'Initial notes',
    };

    const { result, rerender } = renderHook(
      ({ plan }) => useTreatmentPlanForm(plan),
      { initialProps: { plan: initialPlan } }
    );

    expect(result.current.formData.title).toBe('Initial Title');

    const updatedPlan: TreatmentPlan = {
      ...initialPlan,
      title: 'Updated Title',
    };

    rerender({ plan: updatedPlan });

    expect(result.current.formData.title).toBe('Updated Title');
  });
});
