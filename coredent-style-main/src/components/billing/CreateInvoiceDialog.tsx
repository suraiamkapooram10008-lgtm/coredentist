// ============================================
// CoreDent PMS - Create Invoice Dialog
// Dialog for creating new invoices
// ============================================

import React, { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { format, addDays } from 'date-fns';
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
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Plus, Trash2 } from 'lucide-react';
import { PROCEDURE_TEMPLATES } from '@/types/treatmentPlan';

const lineItemSchema = z.object({
  procedureCode: z.string().min(1, 'Required'),
  description: z.string().min(1, 'Required'),
  toothNumber: z.string().optional(),
  quantity: z.number().min(1, 'Min 1'),
  unitPrice: z.number().min(0, 'Must be positive'),
  discount: z.number().min(0, 'Must be positive'),
});

const invoiceSchema = z.object({
  patientName: z.string().trim().min(1, 'Patient name is required').max(100),
  patientEmail: z.string().email('Invalid email').optional().or(z.literal('')),
  patientPhone: z.string().max(20).optional(),
  lineItems: z.array(lineItemSchema).min(1, 'At least one item required'),
  dueInDays: z.number().min(1).max(365),
  notes: z.string().max(500).optional(),
});

type InvoiceFormValues = z.infer<typeof invoiceSchema>;

interface CreateInvoiceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: {
    patientId: string;
    patientName: string;
    patientEmail?: string;
    patientPhone?: string;
    lineItems: {
      procedureCode: string;
      description: string;
      toothNumber?: number;
      quantity: number;
      unitPrice: number;
      discount: number;
    }[];
    dueDate: string;
    notes?: string;
  }) => void;
}

export function CreateInvoiceDialog({
  open,
  onOpenChange,
  onSubmit,
}: CreateInvoiceDialogProps) {
  const form = useForm<InvoiceFormValues>({
    resolver: zodResolver(invoiceSchema),
    defaultValues: {
      patientName: '',
      patientEmail: '',
      patientPhone: '',
      lineItems: [
        {
          procedureCode: '',
          description: '',
          toothNumber: '',
          quantity: 1,
          unitPrice: 0,
          discount: 0,
        },
      ],
      dueInDays: 30,
      notes: '',
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'lineItems',
  });

  const watchedItems = form.watch('lineItems');
  const subtotal = watchedItems.reduce(
    (sum, item) => sum + (item.quantity || 0) * (item.unitPrice || 0),
    0
  );
  const discountTotal = watchedItems.reduce(
    (sum, item) => sum + (item.discount || 0),
    0
  );
  const total = subtotal - discountTotal;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const handleProcedureSelect = (index: number, code: string) => {
    const procedure = PROCEDURE_TEMPLATES.find(p => p.code === code);
    if (procedure) {
      form.setValue(`lineItems.${index}.procedureCode`, procedure.code);
      form.setValue(`lineItems.${index}.description`, procedure.name);
      form.setValue(`lineItems.${index}.unitPrice`, procedure.defaultCost);
    }
  };

  const handleSubmit = (values: InvoiceFormValues) => {
    const dueDate = format(addDays(new Date(), values.dueInDays), 'yyyy-MM-dd');
    
    onSubmit({
      patientId: `patient-${Date.now()}`,
      patientName: values.patientName,
      patientEmail: values.patientEmail || undefined,
      patientPhone: values.patientPhone || undefined,
      lineItems: values.lineItems.map(item => ({
        procedureCode: item.procedureCode,
        description: item.description,
        toothNumber: item.toothNumber ? parseInt(item.toothNumber) : undefined,
        quantity: item.quantity,
        unitPrice: item.unitPrice,
        discount: item.discount,
      })),
      dueDate,
      notes: values.notes || undefined,
    });

    form.reset();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Create Invoice</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="flex flex-col flex-1 overflow-hidden">
            <ScrollArea className="flex-1 -mx-6 px-6">
              <div className="space-y-4 pb-4">
                {/* Patient info */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <FormField
                    control={form.control}
                    name="patientName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Patient Name</FormLabel>
                        <FormControl>
                          <Input placeholder="John Doe" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="patientEmail"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Email (optional)</FormLabel>
                        <FormControl>
                          <Input type="email" placeholder="email@example.com" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="patientPhone"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Phone (optional)</FormLabel>
                        <FormControl>
                          <Input placeholder="(555) 123-4567" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <Separator />

                {/* Line items */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <FormLabel>Line Items</FormLabel>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => append({
                        procedureCode: '',
                        description: '',
                        toothNumber: '',
                        quantity: 1,
                        unitPrice: 0,
                        discount: 0,
                      })}
                    >
                      <Plus className="h-4 w-4 mr-1" />
                      Add Item
                    </Button>
                  </div>

                  {fields.map((field, index) => (
                    <div key={field.id} className="p-3 border rounded-lg space-y-3">
                      <div className="flex items-start gap-2">
                        <div className="flex-1 grid grid-cols-2 gap-2">
                          <FormField
                            control={form.control}
                            name={`lineItems.${index}.procedureCode`}
                            render={({ field }) => (
                              <FormItem>
                                <Select
                                  onValueChange={(value) => handleProcedureSelect(index, value)}
                                  value={field.value}
                                >
                                  <FormControl>
                                    <SelectTrigger>
                                      <SelectValue placeholder="Select procedure" />
                                    </SelectTrigger>
                                  </FormControl>
                                  <SelectContent className="max-h-[200px]">
                                    {PROCEDURE_TEMPLATES.map(proc => (
                                      <SelectItem key={proc.code} value={proc.code}>
                                        <span className="font-mono text-xs">{proc.code}</span> - {proc.name}
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
                            name={`lineItems.${index}.toothNumber`}
                            render={({ field }) => (
                              <FormItem>
                                <FormControl>
                                  <Input placeholder="Tooth # (optional)" {...field} />
                                </FormControl>
                              </FormItem>
                            )}
                          />
                        </div>
                        {fields.length > 1 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="text-destructive"
                            onClick={() => remove(index)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-3 gap-2">
                        <FormField
                          control={form.control}
                          name={`lineItems.${index}.quantity`}
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel className="text-xs">Qty</FormLabel>
                              <FormControl>
                                <Input
                                  type="number"
                                  min={1}
                                  {...field}
                                  onChange={e => field.onChange(parseInt(e.target.value) || 1)}
                                />
                              </FormControl>
                            </FormItem>
                          )}
                        />
                        <FormField
                          control={form.control}
                          name={`lineItems.${index}.unitPrice`}
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel className="text-xs">Unit Price ($)</FormLabel>
                              <FormControl>
                                <Input
                                  type="number"
                                  min={0}
                                  step={0.01}
                                  {...field}
                                  onChange={e => field.onChange(parseFloat(e.target.value) || 0)}
                                />
                              </FormControl>
                            </FormItem>
                          )}
                        />
                        <FormField
                          control={form.control}
                          name={`lineItems.${index}.discount`}
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel className="text-xs">Discount ($)</FormLabel>
                              <FormControl>
                                <Input
                                  type="number"
                                  min={0}
                                  step={0.01}
                                  {...field}
                                  onChange={e => field.onChange(parseFloat(e.target.value) || 0)}
                                />
                              </FormControl>
                            </FormItem>
                          )}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                {/* Totals */}
                <div className="bg-muted/50 p-4 rounded-lg space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>Subtotal:</span>
                    <span>{formatCurrency(subtotal)}</span>
                  </div>
                  {discountTotal > 0 && (
                    <div className="flex justify-between text-green-600">
                      <span>Discounts:</span>
                      <span>-{formatCurrency(discountTotal)}</span>
                    </div>
                  )}
                  <Separator className="my-2" />
                  <div className="flex justify-between font-semibold text-base">
                    <span>Total:</span>
                    <span>{formatCurrency(total)}</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="dueInDays"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Due In (days)</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min={1}
                            max={365}
                            {...field}
                            onChange={e => field.onChange(parseInt(e.target.value) || 30)}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={form.control}
                  name="notes"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Notes (optional)</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="Additional notes for the invoice..."
                          className="resize-none"
                          rows={2}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </ScrollArea>

            <DialogFooter className="pt-4 border-t mt-4">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit">Create Invoice</Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
