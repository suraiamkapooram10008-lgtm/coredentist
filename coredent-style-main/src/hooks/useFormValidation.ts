/**
 * Generic Form Validation Hook
 * Eliminates duplication across form validation logic
 * Provides standardized validation, error handling, and state management
 */

import { useState, useCallback } from 'react';
import type { FormStateType } from '@/types/state';

// ============================================
// Validation Types
// ============================================

/**
 * Validation rule for a field
 */
export type ValidationRule<T = unknown> = {
  validate: (value: T) => boolean | string;
  message?: string;
};

/**
 * Validation schema for a form
 */
export type ValidationSchema<T extends Record<string, unknown>> = {
  [K in keyof T]?: ValidationRule<T[K]>[];
};

/**
 * Form validation result
 */
export interface ValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
}

// ============================================
// Validation Functions
// ============================================

/**
 * Common validation rules
 */
export const validators = {
  /**
   * Required field validator
   */
  required: (message = 'This field is required'): ValidationRule => ({
    validate: (value: unknown) => {
      if (typeof value === 'string') return value.trim().length > 0;
      if (Array.isArray(value)) return value.length > 0;
      return value !== null && value !== undefined;
    },
    message,
  }),

  /**
   * Email validator
   */
  email: (message = 'Invalid email address'): ValidationRule => ({
    validate: (value: unknown) => {
      if (typeof value !== 'string') return false;
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(value);
    },
    message,
  }),

  /**
   * Minimum length validator
   */
  minLength: (min: number, message?: string): ValidationRule => ({
    validate: (value: unknown) => {
      if (typeof value === 'string') return value.length >= min;
      if (Array.isArray(value)) return value.length >= min;
      return false;
    },
    message: message || `Minimum length is ${min}`,
  }),

  /**
   * Maximum length validator
   */
  maxLength: (max: number, message?: string): ValidationRule => ({
    validate: (value: unknown) => {
      if (typeof value === 'string') return value.length <= max;
      if (Array.isArray(value)) return value.length <= max;
      return false;
    },
    message: message || `Maximum length is ${max}`,
  }),

  /**
   * Pattern validator
   */
  pattern: (pattern: RegExp, message = 'Invalid format'): ValidationRule => ({
    validate: (value: unknown) => {
      if (typeof value !== 'string') return false;
      return pattern.test(value);
    },
    message,
  }),

  /**
   * Number range validator
   */
  range: (min: number, max: number, message?: string): ValidationRule => ({
    validate: (value: unknown) => {
      if (typeof value !== 'number') return false;
      return value >= min && value <= max;
    },
    message: message || `Value must be between ${min} and ${max}`,
  }),

  /**
   * Custom validator
   */
  custom: (validate: (value: unknown) => boolean, message = 'Invalid value'): ValidationRule => ({
    validate,
    message,
  }),
};

// ============================================
// Validation Hook
// ============================================

/**
 * Generic form validation hook
 * Replaces 10+ similar validation hooks
 *
 * @example
 * const { values, errors, touched, handleChange, handleBlur, validate } = useFormValidation(
 *   { name: '', email: '' },
 *   {
 *     name: [validators.required(), validators.minLength(2)],
 *     email: [validators.required(), validators.email()],
 *   }
 * );
 */
export function useFormValidation<T extends Record<string, unknown>>(
  initialValues: T,
  schema?: ValidationSchema<T>,
  options?: {
    validateOnChange?: boolean;
    validateOnBlur?: boolean;
  }
) {
  const { validateOnChange = false, validateOnBlur = true } = options || {};

  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  /**
   * Validate a single field
   */
  const validateField = useCallback(
    (fieldName: keyof T, value: unknown): string | undefined => {
      const rules = schema?.[fieldName];
      if (!rules) return undefined;

      for (const rule of rules) {
        const result = rule.validate(value);
        if (result !== true) {
          return typeof result === 'string' ? result : rule.message || 'Invalid value';
        }
      }

      return undefined;
    },
    [schema]
  );

  /**
   * Validate all fields
   */
  const validate = useCallback((): ValidationResult => {
    const newErrors: Record<string, string> = {};
    let isValid = true;

    Object.keys(values).forEach((fieldName) => {
      const error = validateField(fieldName as keyof T, values[fieldName as keyof T]);
      if (error) {
        newErrors[fieldName] = error;
        isValid = false;
      }
    });

    setErrors(newErrors);
    return { isValid, errors: newErrors };
  }, [values, validateField]);

  /**
   * Handle field change
   */
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const { name, value, type } = e.target;
      const fieldValue = type === 'checkbox' ? (e.target as HTMLInputElement).checked : value;

      setValues((prev) => ({
        ...prev,
        [name]: fieldValue,
      }));

      if (validateOnChange) {
        const error = validateField(name as keyof T, fieldValue);
        setErrors((prev) => ({
          ...prev,
          [name]: error || '',
        }));
      }
    },
    [validateOnChange, validateField]
  );

  /**
   * Handle field blur
   */
  const handleBlur = useCallback(
    (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const { name } = e.target;

      setTouched((prev) => ({
        ...prev,
        [name]: true,
      }));

      if (validateOnBlur) {
        const error = validateField(name as keyof T, values[name as keyof T]);
        setErrors((prev) => ({
          ...prev,
          [name]: error || '',
        }));
      }
    },
    [validateOnBlur, validateField, values]
  );

  /**
   * Handle form submission
   */
  const handleSubmit = useCallback(
    async (onSubmit: (values: T) => void | Promise<void>) => {
      return async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();

        const { isValid } = validate();
        if (!isValid) return;

        setIsSubmitting(true);
        try {
          await onSubmit(values);
        } finally {
          setIsSubmitting(false);
        }
      };
    },
    [validate, values]
  );

  /**
   * Reset form to initial values
   */
  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
  }, [initialValues]);

  /**
   * Set field value programmatically
   */
  const setFieldValue = useCallback((fieldName: keyof T, value: unknown) => {
    setValues((prev) => ({
      ...prev,
      [fieldName]: value,
    }));
  }, []);

  /**
   * Set field error programmatically
   */
  const setFieldError = useCallback((fieldName: string, error: string) => {
    setErrors((prev) => ({
      ...prev,
      [fieldName]: error,
    }));
  }, []);

  /**
   * Get form state
   */
  const getFormState = useCallback((): FormStateType => {
    const isDirty = JSON.stringify(values) !== JSON.stringify(initialValues);
    const isValid = Object.keys(errors).length === 0;

    return {
      isSubmitting,
      isValid,
      isDirty,
      errors,
      touched,
    };
  }, [values, initialValues, errors, touched, isSubmitting]);

  return {
    values,
    errors,
    touched,
    isSubmitting,
    handleChange,
    handleBlur,
    handleSubmit,
    validate,
    reset,
    setFieldValue,
    setFieldError,
    getFormState,
  };
}

/**
 * Hook for validating a single field
 * Useful for inline validation
 *
 * @example
 * const { error, validate } = useFieldValidation(
 *   'email',
 *   [validators.required(), validators.email()]
 * );
 */
export function useFieldValidation(
  fieldName: string,
  rules?: ValidationRule[],
  options?: {
    validateOnChange?: boolean;
  }
) {
  const { validateOnChange = false } = options || {};
  const [value, setValue] = useState('');
  const [error, setError] = useState<string | undefined>();

  const validate = useCallback(
    (val: unknown): string | undefined => {
      if (!rules) return undefined;

      for (const rule of rules) {
        const result = rule.validate(val);
        if (result !== true) {
          return typeof result === 'string' ? result : rule.message || 'Invalid value';
        }
      }

      return undefined;
    },
    [rules]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      const newValue = e.target.value;
      setValue(newValue);

      if (validateOnChange) {
        const err = validate(newValue);
        setError(err);
      }
    },
    [validate, validateOnChange]
  );

  const handleBlur = useCallback(() => {
    const err = validate(value);
    setError(err);
  }, [validate, value]);

  return {
    value,
    error,
    setValue,
    setError,
    handleChange,
    handleBlur,
    validate,
  };
}
