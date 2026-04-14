/**
 * usePatientVirtualization Hook
 * Manages virtualization logic for patient lists
 */

import { useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { Patient } from '@/types/api';

interface VirtualizationOptions {
  estimateSize?: number;
  overscan?: number;
}

/**
 * Custom hook for virtualizing patient lists
 */
export function usePatientVirtualization(
  patients: Patient[] = [],
  options: VirtualizationOptions = {}
) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { estimateSize = 120, overscan = 5 } = options;

  const rowVirtualizer = useVirtualizer({
    count: patients.length,
    getScrollElement: () => containerRef.current,
    estimateSize: () => estimateSize,
    overscan,
  });

  return {
    containerRef,
    rowVirtualizer,
    virtualItems: rowVirtualizer.getVirtualItems(),
    totalSize: rowVirtualizer.getTotalSize(),
  };
}
