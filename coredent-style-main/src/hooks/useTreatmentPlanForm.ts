/**
 * useTreatmentPlanForm Hook
 * Manages treatment plan form state and validation
 */

import { useState, useEffect } from 'react';
import type { TreatmentPlan } from '@/types/treatmentPlan';

interface FormValues {
  title: string;
  description: string;
  patientId: string;
  patientName: string;
  notes: string;
}

/**
 * Custom hook for managing treatment plan form state
 */
export function useTreatmentPlanForm(initialPlan?: TreatmentPlan | null) {
  const [formData, setFormData] = useState<FormValues>({
    title: initialPlan?.title || '',
    description: initialPlan?.description || '',
    patientId: initialPlan?.patientId || '',
    patientName: initialPlan?.patientName || '',
    notes: initialPlan?.notes || '',
  });

  const [errors, setErrors] = useState<Partial<FormValues>>({});

  // Reset form when plan changes
  useEffect(() => {
    if (initialPlan) {
      setFormData({
        title: initialPlan.title || '',
        description: initialPlan.description || '',
        patientId: initialPlan.patientId || '',
        patientName: initialPlan.patientName || '',
        notes: initialPlan.notes || '',
      });
    }
  }, [initialPlan]);

  const updateField = (field: keyof FormValues, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  const validate = (): boolean => {
    const newErrors: Partial<FormValues> = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    } else if (formData.title.length > 100) {
      newErrors.title = 'Title too long';
    }

    if (formData.description && formData.description.length > 500) {
      newErrors.description = 'Description too long';
    }

    if (!formData.patientName.trim()) {
      newErrors.patientName = 'Patient name is required';
    }

    if (formData.notes && formData.notes.length > 1000) {
      newErrors.notes = 'Notes too long';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const reset = () => {
    setFormData({
      title: '',
      description: '',
      patientId: '',
      patientName: '',
      notes: '',
    });
    setErrors({});
  };

  return {
    formData,
    errors,
    updateField,
    validate,
    reset,
  };
}
