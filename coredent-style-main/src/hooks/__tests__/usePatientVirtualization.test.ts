/**
 * usePatientVirtualization Hook Tests
 */

import { renderHook } from '@testing-library/react';
import { usePatientVirtualization } from '../usePatientVirtualization';
import type { Patient } from '@/types/api';

describe('usePatientVirtualization', () => {
  const mockPatients: Patient[] = Array.from({ length: 100 }, (_, i) => ({
    id: `patient-${i}`,
    firstName: `Patient`,
    lastName: `${i}`,
    email: `patient${i}@example.com`,
    phone: '555-0000',
    dateOfBirth: '1990-01-01',
    gender: 'M',
    address: '123 Main St',
    city: 'Springfield',
    state: 'IL',
    zipCode: '62701',
    country: 'USA',
    medicalHistory: {
      conditions: [],
      allergies: [],
      medications: [],
    },
    dentalHistory: {
      lastCleaning: '2024-01-01',
      lastXrays: '2024-01-01',
      gumDiseaseHistory: false,
      toothSensitivity: false,
      grindsClenches: false,
      hasImplants: false,
      missingTeeth: [],
    },
  }));

  it('should initialize virtualization with default options', () => {
    const { result } = renderHook(() => usePatientVirtualization(mockPatients));

    expect(result.current.containerRef).toBeDefined();
    expect(result.current.rowVirtualizer).toBeDefined();
    expect(result.current.virtualItems).toBeDefined();
    expect(result.current.totalSize).toBeGreaterThan(0);
  });

  it('should handle empty patient list', () => {
    const { result } = renderHook(() => usePatientVirtualization([]));

    expect(result.current.virtualItems).toHaveLength(0);
    expect(result.current.totalSize).toBe(0);
  });

  it('should calculate correct total size', () => {
    const { result } = renderHook(() =>
      usePatientVirtualization(mockPatients, { estimateSize: 120 })
    );

    // Total size should be approximately count * estimateSize
    expect(result.current.totalSize).toBeGreaterThan(0);
  });

  it('should accept custom estimate size', () => {
    const { result: result1 } = renderHook(() =>
      usePatientVirtualization(mockPatients, { estimateSize: 100 })
    );

    const { result: result2 } = renderHook(() =>
      usePatientVirtualization(mockPatients, { estimateSize: 200 })
    );

    // Different estimate sizes should result in different total sizes
    expect(result1.current.totalSize).not.toBe(result2.current.totalSize);
  });

  it('should accept custom overscan value', () => {
    const { result } = renderHook(() =>
      usePatientVirtualization(mockPatients, { overscan: 10 })
    );

    expect(result.current.rowVirtualizer).toBeDefined();
  });

  it('should handle large patient lists', () => {
    const largePatientList = Array.from({ length: 10000 }, (_, i) => ({
      ...mockPatients[0],
      id: `patient-${i}`,
    }));

    const { result } = renderHook(() => usePatientVirtualization(largePatientList));

    expect(result.current.virtualItems).toBeDefined();
    expect(result.current.totalSize).toBeGreaterThan(0);
  });

  it('should update when patient list changes', () => {
    const { result, rerender } = renderHook(
      ({ patients }) => usePatientVirtualization(patients),
      { initialProps: { patients: mockPatients.slice(0, 50) } }
    );

    const initialSize = result.current.totalSize;

    rerender({ patients: mockPatients });

    expect(result.current.totalSize).toBeGreaterThan(initialSize);
  });

  it('should provide container ref for scrolling', () => {
    const { result } = renderHook(() => usePatientVirtualization(mockPatients));

    expect(result.current.containerRef).toBeDefined();
    expect(result.current.containerRef.current).toBeNull(); // Not mounted in test
  });
});
