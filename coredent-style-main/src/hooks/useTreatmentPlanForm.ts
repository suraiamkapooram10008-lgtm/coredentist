import { useState, useEffect, useCallback, useRef } from 'react';
import type { TreatmentPlan } from '@/types/treatmentPlan';

export interface FormData {
  title: string;
  description: string;
  patientName: string;
  notes: string;
}

export interface FormErrors {
  title?: string;
  description?: string;
  patientName?: string;
  notes?: string;
}

function getInitialFormData(plan?: TreatmentPlan | null): FormData {
  return {
    title: plan?.title || '',
    description: plan?.description || '',
    patientName: plan?.patientName || '',
    notes: plan?.notes || '',
  };
}

export function useTreatmentPlanForm(plan?: TreatmentPlan | null) {
  const [formData, setFormData] = useState<FormData>(() => getInitialFormData(plan));
  const [errors, setErrors] = useState<FormErrors>({});
  const formDataRef = useRef<FormData>(formData);

  useEffect(() => {
    formDataRef.current = formData;
  }, [formData]);

  useEffect(() => {
    const initial = getInitialFormData(plan);
    setFormData(initial);
    formDataRef.current = initial;
    setErrors({});
  }, [plan]);

  const updateField = useCallback((field: keyof FormData, value: string) => {
    const next = { ...formDataRef.current, [field]: value };
    formDataRef.current = next;
    setFormData(next);
    setErrors((prev) => {
      const nextErrors = { ...prev };
      delete nextErrors[field];
      return nextErrors;
    });
  }, []);

  const validate = useCallback((): boolean => {
    const currentFormData = formDataRef.current;
    const nextErrors: FormErrors = {};
    if (!currentFormData.title.trim()) {
      nextErrors.title = 'Title is required';
    } else if (currentFormData.title.length > 100) {
      nextErrors.title = 'Title too long';
    }
    if (!currentFormData.patientName.trim()) {
      nextErrors.patientName = 'Patient name is required';
    }
    if (currentFormData.description && currentFormData.description.length > 500) {
      nextErrors.description = 'Description too long';
    }
    if (currentFormData.notes && currentFormData.notes.length > 1000) {
      nextErrors.notes = 'Notes too long';
    }
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }, []);

  const reset = useCallback(() => {
    const initial = getInitialFormData(plan);
    setFormData(initial);
    formDataRef.current = initial;
    setErrors({});
  }, [plan]);

  return {
    formData,
    errors,
    updateField,
    validate,
    reset,
  };
}
