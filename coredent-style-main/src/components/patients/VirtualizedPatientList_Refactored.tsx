/**
 * VirtualizedPatientList Component (Refactored)
 * High-performance patient list with virtualization
 */

import React from 'react';
import { PatientCard } from './PatientCard.memo';
import { PatientListEmpty } from './PatientListEmpty';
import { usePatientVirtualization } from '@/hooks/usePatientVirtualization';
import type { Patient } from '@/types/api';

interface VirtualizedPatientListProps {
  patients: Patient[];
  onSelect?: (patient: Patient) => void;
  onPatientClick?: (patient: Patient) => void;
  isLoading?: boolean;
  containerRef?: React.RefObject<HTMLDivElement>;
}

/**
 * VirtualizedPatientList - High-performance patient list with virtualization
 *
 * This component uses @tanstack/react-virtual to efficiently render large patient lists
 * by only rendering visible items in the viewport. This significantly improves performance
 * when dealing with thousands of patients.
 *
 * Features:
 * - Virtual scrolling for large datasets
 * - Smooth scrolling experience
 * - Memory efficient rendering
 * - Customizable item rendering
 */
export function VirtualizedPatientList({
  patients,
  onPatientClick,
  isLoading = false,
  containerRef: externalContainerRef,
}: VirtualizedPatientListProps) {
  const { containerRef: internalRef, virtualItems, totalSize } =
    usePatientVirtualization(patients, {
      estimateSize: 120,
      overscan: 5,
    });

  const containerRef = externalContainerRef || internalRef;

  // Show empty state
  if (!isLoading && patients.length === 0) {
    return <PatientListEmpty isLoading={false} />;
  }

  // Show loading state
  if (isLoading) {
    return <PatientListEmpty isLoading={true} />;
  }

  return (
    <div
      ref={containerRef}
      className="h-[calc(100vh-200px)] overflow-auto"
      style={{ contain: 'strict' }}
    >
      <div
        style={{
          height: `${totalSize}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualItems.map((virtualRow) => {
          const patient = patients[virtualRow.index];
          return (
            <div
              key={patient.id}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <PatientCard
                patient={patient}
                onSelect={() => onPatientClick?.(patient)}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
