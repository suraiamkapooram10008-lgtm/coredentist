// ============================================
// CoreDent PMS - Add Procedure Dialog
// Dialog for adding a procedure to a tooth
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
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { PROCEDURE_CODES, type ToothSurface, type ProcedureStatus } from '@/types/dentalChart';

const procedureSchema = z.object({
  procedureCode: z.string().min(1, 'Please select a procedure'),
  status: z.enum(['planned', 'in_progress', 'completed']),
  surfaces: z.array(z.string()).optional(),
  notes: z.string().optional(),
});

type ProcedureFormValues = z.infer<typeof procedureSchema>;

interface AddProcedureDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  toothNumber: number;
  toothName: string;
  onSubmit: (data: {
    procedureCode: string;
    procedureName: string;
    status: ProcedureStatus;
    surfaces: ToothSurface[];
    notes?: string;
    color: string;
  }) => void;
}

const SURFACES: { value: ToothSurface; label: string }[] = [
  { value: 'mesial', label: 'Mesial (M)' },
  { value: 'distal', label: 'Distal (D)' },
  { value: 'occlusal', label: 'Occlusal (O)' },
  { value: 'buccal', label: 'Buccal (B)' },
  { value: 'lingual', label: 'Lingual (L)' },
  { value: 'facial', label: 'Facial (F)' },
  { value: 'incisal', label: 'Incisal (I)' },
];

export function AddProcedureDialog({
  open,
  onOpenChange,
  toothNumber,
  toothName,
  onSubmit,
}: AddProcedureDialogProps) {
  const form = useForm<ProcedureFormValues>({
    resolver: zodResolver(procedureSchema),
    defaultValues: {
      procedureCode: '',
      status: 'planned',
      surfaces: [],
      notes: '',
    },
  });

  const handleSubmit = (values: ProcedureFormValues) => {
    const procedure = PROCEDURE_CODES.find(p => p.code === values.procedureCode);
    if (!procedure) return;
    
    onSubmit({
      procedureCode: procedure.code,
      procedureName: procedure.name,
      status: values.status,
      surfaces: (values.surfaces || []) as ToothSurface[],
      notes: values.notes,
      color: procedure.color,
    });
    
    form.reset();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add Procedure</DialogTitle>
          <p className="text-sm text-muted-foreground">
            Tooth #{toothNumber} - {toothName}
          </p>
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
                    <SelectContent>
                      {PROCEDURE_CODES.map(proc => (
                        <SelectItem key={proc.code} value={proc.code}>
                          <div className="flex items-center gap-2">
                            <div
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: proc.color }}
                            />
                            <span className="font-mono text-xs">{proc.code}</span>
                            <span className="text-sm">{proc.name}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="status"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Status</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="planned">Planned</SelectItem>
                      <SelectItem value="in_progress">In Progress</SelectItem>
                      <SelectItem value="completed">Completed</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="surfaces"
              render={() => (
                <FormItem>
                  <FormLabel>Tooth Surfaces</FormLabel>
                  <div className="grid grid-cols-2 gap-2 pt-1">
                    {SURFACES.map(surface => (
                      <FormField
                        key={surface.value}
                        control={form.control}
                        name="surfaces"
                        render={({ field }) => (
                          <FormItem className="flex items-center space-x-2 space-y-0">
                            <FormControl>
                              <Checkbox
                                checked={field.value?.includes(surface.value)}
                                onCheckedChange={(checked) => {
                                  const current = field.value || [];
                                  if (checked) {
                                    field.onChange([...current, surface.value]);
                                  } else {
                                    field.onChange(
                                      current.filter((v) => v !== surface.value)
                                    );
                                  }
                                }}
                              />
                            </FormControl>
                            <Label className="text-sm font-normal cursor-pointer">
                              {surface.label}
                            </Label>
                          </FormItem>
                        )}
                      />
                    ))}
                  </div>
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
                      placeholder="Add any relevant notes..."
                      className="resize-none"
                      rows={3}
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
