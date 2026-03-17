// ============================================
// CoreDent PMS - Treatment Timeline View
// Visual timeline of treatment procedures
// ============================================

import React from 'react';
import { format } from 'date-fns';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  CheckCircle2, 
  Circle, 
  Clock, 
  MoreVertical, 
  Trash2,
  Calendar,
  DollarSign
} from 'lucide-react';
import type { TreatmentProcedure, ProcedurePhase } from '@/types/treatmentPlan';
import { PHASE_CONFIG } from '@/types/treatmentPlan';
import { cn } from '@/lib/utils';

interface TreatmentTimelineProps {
  procedures: TreatmentProcedure[];
  onCompleteProcedure: (procedureId: string) => void;
  onDeleteProcedure: (procedureId: string) => void;
  readOnly?: boolean;
}

export function TreatmentTimeline({
  procedures,
  onCompleteProcedure,
  onDeleteProcedure,
  readOnly = false,
}: TreatmentTimelineProps) {
  // Group procedures by phase
  const groupedByPhase = procedures.reduce((acc, proc) => {
    if (!acc[proc.phase]) {
      acc[proc.phase] = [];
    }
    acc[proc.phase].push(proc);
    return acc;
  }, {} as Record<ProcedurePhase, TreatmentProcedure[]>);

  // Sort phases by order
  const sortedPhases = Object.entries(groupedByPhase)
    .sort(([a], [b]) => PHASE_CONFIG[a as ProcedurePhase].order - PHASE_CONFIG[b as ProcedurePhase].order);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const getStatusIcon = (status: TreatmentProcedure['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-600" />;
      case 'scheduled':
        return <Clock className="h-5 w-5 text-amber-600" />;
      default:
        return <Circle className="h-5 w-5 text-muted-foreground" />;
    }
  };

  if (procedures.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p>No procedures in this treatment plan yet.</p>
        <p className="text-sm mt-1">Add procedures to build the treatment timeline.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {sortedPhases.map(([phase, procs]) => {
        const phaseConfig = PHASE_CONFIG[phase as ProcedurePhase];
        const completedCount = procs.filter(p => p.status === 'completed').length;
        const phaseTotal = procs.reduce((sum, p) => sum + p.estimatedCost, 0);

        return (
          <div key={phase} className="space-y-3">
            {/* Phase header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge className={cn('font-medium', phaseConfig.color)}>
                  {phaseConfig.label}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  {completedCount}/{procs.length} completed
                </span>
              </div>
              <span className="text-sm font-medium">
                {formatCurrency(phaseTotal)}
              </span>
            </div>

            {/* Procedures in this phase */}
            <div className="relative pl-6 border-l-2 border-muted space-y-3">
              {procs.map((procedure, index) => (
                <div
                  key={procedure.id}
                  className={cn(
                    'relative',
                    procedure.status === 'completed' && 'opacity-75'
                  )}
                >
                  {/* Timeline dot */}
                  <div className="absolute -left-[calc(1.5rem+5px)] bg-background">
                    {getStatusIcon(procedure.status)}
                  </div>

                  <Card className={cn(
                    'transition-colors',
                    procedure.status === 'completed' && 'bg-muted/50'
                  )}>
                    <CardContent className="py-3 px-4">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            {!readOnly && procedure.status !== 'completed' && (
                              <Checkbox
                                checked={false}
                                onCheckedChange={() => onCompleteProcedure(procedure.id)}
                                className="mt-0.5"
                              />
                            )}
                            <div className="flex-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <Badge variant="outline" className="font-mono text-xs">
                                  {procedure.procedureCode}
                                </Badge>
                                {procedure.toothNumber && (
                                  <Badge variant="secondary" className="text-xs">
                                    Tooth #{procedure.toothNumber}
                                  </Badge>
                                )}
                              </div>
                              <p className={cn(
                                'font-medium mt-1',
                                procedure.status === 'completed' && 'line-through'
                              )}>
                                {procedure.procedureName}
                              </p>
                            </div>
                          </div>

                          {/* Details row */}
                          <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <DollarSign className="h-3.5 w-3.5" />
                              {procedure.status === 'completed' && procedure.actualCost
                                ? formatCurrency(procedure.actualCost)
                                : formatCurrency(procedure.estimatedCost)}
                              {procedure.status === 'completed' && procedure.actualCost !== procedure.estimatedCost && (
                                <span className="text-xs">
                                  (est. {formatCurrency(procedure.estimatedCost)})
                                </span>
                              )}
                            </span>
                            {procedure.scheduledDate && (
                              <span className="flex items-center gap-1">
                                <Calendar className="h-3.5 w-3.5" />
                                {format(new Date(procedure.scheduledDate), 'MMM d, yyyy')}
                              </span>
                            )}
                            {procedure.completedDate && (
                              <span className="flex items-center gap-1 text-green-600">
                                <CheckCircle2 className="h-3.5 w-3.5" />
                                {format(new Date(procedure.completedDate), 'MMM d, yyyy')}
                              </span>
                            )}
                          </div>

                          {procedure.notes && (
                            <p className="text-sm text-muted-foreground mt-2 italic">
                              {procedure.notes}
                            </p>
                          )}
                        </div>

                        {!readOnly && (
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              {procedure.status !== 'completed' && (
                                <DropdownMenuItem onClick={() => onCompleteProcedure(procedure.id)}>
                                  <CheckCircle2 className="h-4 w-4 mr-2" />
                                  Mark Complete
                                </DropdownMenuItem>
                              )}
                              <DropdownMenuItem
                                onClick={() => onDeleteProcedure(procedure.id)}
                                className="text-destructive focus:text-destructive"
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Remove
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
