// ============================================
// CoreDent PMS - Add Procedure to Plan Dialog
// Dialog for adding procedures to treatment plans
// ============================================

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { PROCEDURE_TEMPLATES, PHASE_CONFIG, type ProcedurePhase } from '@/types/treatmentPlan';

const procedureSchema = z.object({
  procedureCode: z.string().min(1, 'Please select a procedure'),
  toothNumber: z.string().optional(),
  phase: z.enum(['urgent', 'phase_1', 'phase_2', 'phase_3', 'maintenance']),
  estimatedCost: z.number().min(0, 'Cost must be positive'),
  notes: z.string().trim().max(500).optional(),
});

type ProcedureFormValues = z.infer<typeof procedureSchema>;

interface AddProcedureToPlanDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: {
    procedureCode: string;
    procedureName: string;
    toothNumber?: number;
    phase: ProcedurePhase;
    estimatedCost: number;
    notes?: string;
  }) => void;
}

export function AddProcedureToPlanDialog({
  open,
  onOpenChange,
  onSubmit,
}: AddProcedureToPlanDialogProps) {
  const form = useForm<ProcedureFormValues>({
    resolver: zodResolver(procedureSchema),
    defaultValues: {
      procedureCode: '',
      toothNumber: '',
      phase: 'phase_1',
      estimatedCost: 0,
      notes: '',
    },
  });

  const selectedProcedure = PROCEDURE_TEMPLATES.find(
    p => p.code === form.watch('procedureCode')
  );

  React.useEffect(() => {
    if (selectedProcedure) {
      form.setValue('estimatedCost', selectedProcedure.defaultCost);
    }
  }, [selectedProcedure, form]);

  const handleSubmit = (values: ProcedureFormValues) => {
    const procedure = PROCEDURE_TEMPLATES.find(p => p.code === values.procedureCode);
    if (!procedure) return;

    onSubmit({
      procedureCode: procedure.code,
      procedureName: procedure.name,
      toothNumber: values.toothNumber ? parseInt(values.toothNumber) : undefined,
      phase: values.phase,
      estimatedCost: values.estimatedCost,
      notes: values.notes,
    });

    form.reset();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add Procedure to Plan</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="procedureCode"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Procedure</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a procedure" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent className="max-h-[300px]">
                      {PROCEDURE_TEMPLATES.map(proc => (
                        <SelectItem key={proc.code} value={proc.code}>
                          <span className="font-mono text-xs mr-2">{proc.code}</span>
                          {proc.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="toothNumber"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Tooth # (optional)</FormLabel>
                    <FormControl>
                      <Input 
                        type="number" 
                        min={1} 
                        max={32} 
                        placeholder="1-32"
                        {...field} 
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="phase"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Treatment Phase</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {Object.entries(PHASE_CONFIG).map(([value, config]) => (
                          <SelectItem key={value} value={value}>
                            {config.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="estimatedCost"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Estimated Cost ($)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      min={0}
                      step={0.01}
                      {...field}
                      onChange={e => field.onChange(parseFloat(e.target.value) || 0)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="notes"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Notes (optional)</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Additional notes..."
                      className="resize-none"
                      rows={2}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit">Add Procedure</Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
