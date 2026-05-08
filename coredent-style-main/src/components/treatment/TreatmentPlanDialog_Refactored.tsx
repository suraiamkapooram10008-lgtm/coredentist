/**
 * TreatmentPlanDialog Component (Refactored)
 * Create/Edit treatment plan form in a dialog
 */

import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { TreatmentPlanForm } from './TreatmentPlanForm';
import type { TreatmentPlan } from '@/types/treatmentPlan';

interface TreatmentPlanDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  plan?: TreatmentPlan | null;
  onSubmit: (data: {
    title: string;
    description?: string;
    patientId: string;
    patientName: string;
    notes?: string;
  }) => void;
}

/**
 * Dialog wrapper for treatment plan form
 */
export function TreatmentPlanDialog({
  open,
  onOpenChange,
  plan,
  onSubmit,
}: TreatmentPlanDialogProps) {
  const isEditing = !!plan;

  const handleSubmit = (data: {
    title: string;
    description?: string;
    patientId: string;
    patientName: string;
    notes?: string;
  }) => {
    onSubmit(data);
    onOpenChange(false);
  };

  const handleCancel = () => {
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Edit Treatment Plan' : 'Create Treatment Plan'}
          </DialogTitle>
        </DialogHeader>

        <TreatmentPlanForm
          plan={plan}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
        />
      </DialogContent>
    </Dialog>
  );
}
