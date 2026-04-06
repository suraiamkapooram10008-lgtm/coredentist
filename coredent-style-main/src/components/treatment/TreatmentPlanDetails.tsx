// ============================================
// CoreDent PMS - Treatment Plan Details Sheet
// Full view of a treatment plan with procedures
// ============================================

import React, { useState } from 'react';
import { format } from 'date-fns';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Plus, 
  Edit, 
  User, 
  Calendar, 
  DollarSign,
  CheckCircle2,
  FileText
} from 'lucide-react';
import { TreatmentTimeline } from './TreatmentTimeline';
import { AddProcedureToPlanDialog } from './AddProcedureToPlanDialog';
import type { TreatmentPlan, ProcedurePhase } from '@/types/treatmentPlan';
import { STATUS_CONFIG, calculatePlanSummary } from '@/types/treatmentPlan';
import { cn } from '@/lib/utils';

interface TreatmentPlanDetailsProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  plan: TreatmentPlan | null;
  onEdit: () => void;
  onAddProcedure: (data: {
    procedureCode: string;
    procedureName: string;
    toothNumber?: number;
    phase: ProcedurePhase;
    estimatedCost: number;
    notes?: string;
  }) => void;
  onCompleteProcedure: (procedureId: string) => void;
  onDeleteProcedure: (procedureId: string) => void;
}

export function TreatmentPlanDetails({
  open,
  onOpenChange,
  plan,
  onEdit,
  onAddProcedure,
  onCompleteProcedure,
  onDeleteProcedure,
}: TreatmentPlanDetailsProps) {
  const [isAddProcedureOpen, setIsAddProcedureOpen] = useState(false);

  if (!plan) return null;

  const summary = calculatePlanSummary(plan);
  const statusConfig = STATUS_CONFIG[plan.status];

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent className="w-full sm:max-w-2xl overflow-hidden flex flex-col">
          <SheetHeader className="flex-shrink-0">
            <div className="flex items-start justify-between gap-4 pr-8">
              <div className="space-y-1">
                <SheetTitle className="text-xl">{plan.title}</SheetTitle>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <User className="h-4 w-4" />
                  <span>{plan.patientName}</span>
                </div>
              </div>
              <Badge className={cn('capitalize', statusConfig.color)}>
                {statusConfig.label}
              </Badge>
            </div>
          </SheetHeader>

          <ScrollArea className="flex-1 -mx-6 px-6">
            <div className="space-y-6 pb-6">
              {/* Summary cards */}
              <div className="grid grid-cols-3 gap-3">
                <Card>
                  <CardContent className="py-3 px-4 text-center">
                    <DollarSign className="h-5 w-5 mx-auto text-muted-foreground" />
                    <p className="text-lg font-bold mt-1">
                      {formatCurrency(summary.totalEstimatedCost)}
                    </p>
                    <p className="text-xs text-muted-foreground">Total Est.</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="py-3 px-4 text-center">
                    <CheckCircle2 className="h-5 w-5 mx-auto text-green-600" />
                    <p className="text-lg font-bold mt-1">
                      {formatCurrency(summary.totalActualCost)}
                    </p>
                    <p className="text-xs text-muted-foreground">Completed</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="py-3 px-4 text-center">
                    <FileText className="h-5 w-5 mx-auto text-amber-600" />
                    <p className="text-lg font-bold mt-1">
                      {formatCurrency(summary.remainingCost)}
                    </p>
                    <p className="text-xs text-muted-foreground">Remaining</p>
                  </CardContent>
                </Card>
              </div>

              {/* Description */}
              {plan.description && (
                <div>
                  <h4 className="text-sm font-medium mb-2">Description</h4>
                  <p className="text-sm text-muted-foreground">{plan.description}</p>
                </div>
              )}

              {/* Dates */}
              <div className="flex flex-wrap gap-4 text-sm">
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  Created: {format(new Date(plan.createdAt), 'MMM d, yyyy')}
                </div>
                {plan.acceptedAt && (
                  <div className="flex items-center gap-1.5 text-blue-600">
                    <CheckCircle2 className="h-4 w-4" />
                    Accepted: {format(new Date(plan.acceptedAt), 'MMM d, yyyy')}
                  </div>
                )}
                {plan.completedAt && (
                  <div className="flex items-center gap-1.5 text-green-600">
                    <CheckCircle2 className="h-4 w-4" />
                    Completed: {format(new Date(plan.completedAt), 'MMM d, yyyy')}
                  </div>
                )}
              </div>

              <Separator />

              {/* Actions */}
              <div className="flex items-center gap-2">
                <Button onClick={() => setIsAddProcedureOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Procedure
                </Button>
                <Button variant="outline" onClick={onEdit}>
                  <Edit className="h-4 w-4 mr-2" />
                  Edit Plan
                </Button>
              </div>

              {/* Timeline */}
              <div>
                <h4 className="text-sm font-medium mb-4">
                  Treatment Timeline ({summary.completedProcedures}/{summary.totalProcedures} completed)
                </h4>
                <TreatmentTimeline
                  procedures={plan.procedures}
                  onCompleteProcedure={onCompleteProcedure}
                  onDeleteProcedure={onDeleteProcedure}
                />
              </div>

              {/* Notes */}
              {plan.notes && (
                <>
                  <Separator />
                  <div>
                    <h4 className="text-sm font-medium mb-2">Internal Notes</h4>
                    <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                      {plan.notes}
                    </p>
                  </div>
                </>
              )}
            </div>
          </ScrollArea>
        </SheetContent>
      </Sheet>

      <AddProcedureToPlanDialog
        open={isAddProcedureOpen}
        onOpenChange={setIsAddProcedureOpen}
        onSubmit={onAddProcedure}
      />
    </>
  );
}
