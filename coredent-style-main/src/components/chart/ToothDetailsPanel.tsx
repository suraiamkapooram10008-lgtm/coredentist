// ============================================
// CoreDent PMS - Tooth Details Panel
// Shows details and procedures for selected tooth
// ============================================

import React from 'react';
import { format } from 'date-fns';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Plus, Clock, CheckCircle2, AlertCircle, Trash2 } from 'lucide-react';
import type { ToothData, ToothCondition, ProcedureStatus } from '@/types/dentalChart';
import { STATUS_STYLES } from '@/types/dentalChart';
import { cn } from '@/lib/utils';

interface ToothDetailsPanelProps {
  tooth: ToothData | null;
  onAddProcedure: () => void;
  onUpdateCondition: (condition: ToothCondition) => void;
  onUpdateProcedureStatus: (procedureId: string, status: ProcedureStatus) => void;
  onDeleteProcedure: (procedureId: string) => void;
}

const CONDITIONS: { value: ToothCondition; label: string }[] = [
  { value: 'healthy', label: 'Healthy' },
  { value: 'decay', label: 'Decay' },
  { value: 'filling', label: 'Filling' },
  { value: 'crown', label: 'Crown' },
  { value: 'root_canal', label: 'Root Canal' },
  { value: 'extraction', label: 'Extraction Needed' },
  { value: 'missing', label: 'Missing' },
  { value: 'implant', label: 'Implant' },
  { value: 'bridge', label: 'Bridge' },
  { value: 'veneer', label: 'Veneer' },
];

function getStatusIcon(status: ProcedureStatus) {
  switch (status) {
    case 'planned':
      return <Clock className="h-3.5 w-3.5" />;
    case 'in_progress':
      return <AlertCircle className="h-3.5 w-3.5" />;
    case 'completed':
      return <CheckCircle2 className="h-3.5 w-3.5" />;
  }
}

export function ToothDetailsPanel({
  tooth,
  onAddProcedure,
  onUpdateCondition,
  onUpdateProcedureStatus,
  onDeleteProcedure,
}: ToothDetailsPanelProps) {
  if (!tooth) {
    return (
      <Card className="h-full">
        <CardContent className="flex flex-col items-center justify-center h-full min-h-[400px] text-center">
          <div className="text-muted-foreground">
            <p className="text-lg font-medium">No tooth selected</p>
            <p className="text-sm mt-1">Click on a tooth in the chart to view details</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">
            Tooth #{tooth.number}
          </CardTitle>
          <Button size="sm" onClick={onAddProcedure}>
            <Plus className="h-4 w-4 mr-1" />
            Add Procedure
          </Button>
        </div>
        <p className="text-sm text-muted-foreground">{tooth.name}</p>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Condition selector */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Current Condition</label>
          <Select
            value={tooth.condition}
            onValueChange={(value) => onUpdateCondition(value as ToothCondition)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CONDITIONS.map(condition => (
                <SelectItem key={condition.value} value={condition.value}>
                  {condition.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <Separator />
        
        {/* Procedures list */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium">Procedures</h4>
          
          {tooth.procedures.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No procedures recorded for this tooth
            </p>
          ) : (
            <ScrollArea className="h-[280px]">
              <div className="space-y-3 pr-4">
                {tooth.procedures.map(procedure => {
                  const statusStyle = STATUS_STYLES[procedure.status];
                  
                  return (
                    <div
                      key={procedure.id}
                      className={cn(
                        'p-3 rounded-lg border',
                        statusStyle.border,
                        statusStyle.bg
                      )}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <Badge
                              variant="outline"
                              className="text-xs font-mono"
                            >
                              {procedure.procedureCode}
                            </Badge>
                            <Badge
                              variant="secondary"
                              className={cn('text-xs', statusStyle.text)}
                            >
                              {getStatusIcon(procedure.status)}
                              <span className="ml-1 capitalize">{procedure.status.replace('_', ' ')}</span>
                            </Badge>
                          </div>
                          <p className="text-sm font-medium mt-1 truncate">
                            {procedure.procedureName}
                          </p>
                          <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                            <span>{format(new Date(procedure.date), 'MMM d, yyyy')}</span>
                            <span>•</span>
                            <span>{procedure.dentistName}</span>
                          </div>
                          {procedure.surfaces.length > 0 && (
                            <p className="text-xs text-muted-foreground mt-1">
                              Surfaces: {procedure.surfaces.join(', ')}
                            </p>
                          )}
                        </div>
                        
                        <div className="flex flex-col gap-1">
                          <Select
                            value={procedure.status}
                            onValueChange={(value) => 
                              onUpdateProcedureStatus(procedure.id, value as ProcedureStatus)
                            }
                          >
                            <SelectTrigger className="h-7 w-[100px] text-xs">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="planned">Planned</SelectItem>
                              <SelectItem value="in_progress">In Progress</SelectItem>
                              <SelectItem value="completed">Completed</SelectItem>
                            </SelectContent>
                          </Select>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 text-destructive hover:text-destructive"
                            onClick={() => onDeleteProcedure(procedure.id)}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
