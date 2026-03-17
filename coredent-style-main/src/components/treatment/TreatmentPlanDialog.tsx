// ============================================
// CoreDent PMS - Treatment Plan Dialog
// Create/Edit treatment plan form
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
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import type { TreatmentPlan } from '@/types/treatmentPlan';

const planSchema = z.object({
  title: z.string().trim().min(1, 'Title is required').max(100, 'Title too long'),
  description: z.string().trim().max(500, 'Description too long').optional(),
  patientId: z.string().min(1, 'Patient is required'),
  patientName: z.string().min(1, 'Patient name is required'),
  notes: z.string().trim().max(1000, 'Notes too long').optional(),
});

type PlanFormValues = z.infer<typeof planSchema>;

interface TreatmentPlanDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  plan?: TreatmentPlan | null;
  onSubmit: (data: PlanFormValues) => void;
}

export function TreatmentPlanDialog({
  open,
  onOpenChange,
  plan,
  onSubmit,
}: TreatmentPlanDialogProps) {
  const isEditing = !!plan;

  const form = useForm<PlanFormValues>({
    resolver: zodResolver(planSchema),
    defaultValues: {
      title: plan?.title || '',
      description: plan?.description || '',
      patientId: plan?.patientId || '',
      patientName: plan?.patientName || '',
      notes: plan?.notes || '',
    },
  });

  React.useEffect(() => {
    if (open) {
      form.reset({
        title: plan?.title || '',
        description: plan?.description || '',
        patientId: plan?.patientId || '',
        patientName: plan?.patientName || '',
        notes: plan?.notes || '',
      });
    }
  }, [open, plan, form]);

  const handleSubmit = (values: PlanFormValues) => {
    onSubmit(values);
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

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Plan Title</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g., Comprehensive Restoration Plan" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="patientName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Patient</FormLabel>
                  <FormControl>
                    <Input placeholder="Patient name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description (optional)</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Brief description of the treatment plan..."
                      className="resize-none"
                      rows={3}
                      {...field}
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
                  <FormLabel>Internal Notes (optional)</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Notes for the dental team..."
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
              <Button type="submit">
                {isEditing ? 'Save Changes' : 'Create Plan'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
