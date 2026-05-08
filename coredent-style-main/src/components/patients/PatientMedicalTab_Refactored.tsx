/**
 * PatientMedicalTab Component (Refactored)
 * Displays patient medical and dental history with extracted sub-components
 */

import React from 'react';
import { MedicalConditionsCard } from './MedicalConditionsCard';
import { AllergiesCard } from './AllergiesCard';
import { MedicationsCard } from './MedicationsCard';
import { DentalHistoryCard } from './DentalHistoryCard';
import type { PatientRecord } from '@/types/patient';

interface PatientMedicalTabProps {
  medicalHistory: PatientRecord['medicalHistory'];
  dentalHistory: PatientRecord['dentalHistory'];
}

/**
 * Medical tab component with refactored sub-components
 */
export const PatientMedicalTab = React.memo(function PatientMedicalTab({
  medicalHistory,
  dentalHistory,
}: PatientMedicalTabProps) {
  return (
    <div className="grid gap-6 lg:grid-cols-2 animate-in fade-in slide-in-from-bottom-2 duration-500">
      <MedicalConditionsCard conditions={medicalHistory.conditions} />
      <AllergiesCard allergies={medicalHistory.allergies} />
      <MedicationsCard medications={medicalHistory.medications} />
      <DentalHistoryCard dentalHistory={dentalHistory} />
    </div>
  );
});

PatientMedicalTab.displayName = 'PatientMedicalTab';
