// ============================================
// CoreDent PMS - Record Payment Dialog
// Dialog for recording payments on invoices
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
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import type { Invoice, PaymentMethod } from '@/types/billing';
import { PAYMENT_METHODS } from '@/types/billing';

const paymentSchema = z.object({
  amount: z.number().min(0.01, 'Amount must be at least $0.01'),
  method: z.enum(['cash', 'credit_card', 'debit_card', 'check', 'bank_transfer', 'other']),
  reference: z.string().max(100).optional(),
  notes: z.string().max(500).optional(),
});

type PaymentFormValues = z.infer<typeof paymentSchema>;

interface RecordPaymentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  invoice: Invoice | null;
  onSubmit: (data: {
    amount: number;
    method: PaymentMethod;
    reference?: string;
    notes?: string;
  }) => void;
}

export function RecordPaymentDialog({
  open,
  onOpenChange,
  invoice,
  onSubmit,
}: RecordPaymentDialogProps) {
  const form = useForm<PaymentFormValues>({
    resolver: zodResolver(paymentSchema),
    defaultValues: {
      amount: invoice?.balance || 0,
      method: 'credit_card',
      reference: '',
      notes: '',
    },
  });

  React.useEffect(() => {
    if (open && invoice) {
      form.reset({
        amount: invoice.balance,
        method: 'credit_card',
        reference: '',
        notes: '',
      });
    }
  }, [open, invoice, form]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const handleSubmit = (values: PaymentFormValues) => {
    onSubmit({
      amount: values.amount,
      method: values.method,
      reference: values.reference || undefined,
      notes: values.notes || undefined,
    });
    form.reset();
    onOpenChange(false);
  };

  const handlePayInFull = () => {
    if (invoice) {
      form.setValue('amount', invoice.balance);
    }
  };

  if (!invoice) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[450px]">
        <DialogHeader>
          <DialogTitle>Record Payment</DialogTitle>
        </DialogHeader>

        {/* Invoice summary */}
        <div className="bg-muted/50 p-4 rounded-lg space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-mono text-sm">{invoice.invoiceNumber}</span>
            <Badge variant="outline">{invoice.patientName}</Badge>
          </div>
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div>
              <p className="text-muted-foreground">Total</p>
              <p className="font-medium">{formatCurrency(invoice.total)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Paid</p>
              <p className="font-medium text-green-600">{formatCurrency(invoice.amountPaid)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Balance</p>
              <p className="font-medium text-amber-600">{formatCurrency(invoice.balance)}</p>
            </div>
          </div>
        </div>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="amount"
              render={({ field }) => (
                <FormItem>
                  <div className="flex items-center justify-between">
                    <FormLabel>Payment Amount</FormLabel>
                    <Button
                      type="button"
                      variant="link"
                      size="sm"
                      className="h-auto p-0 text-xs"
                      onClick={handlePayInFull}
                    >
                      Pay in full ({formatCurrency(invoice.balance)})
                    </Button>
                  </div>
                  <FormControl>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                        $
                      </span>
                      <Input
                        type="number"
                        min={0.01}
                        max={invoice.balance}
                        step={0.01}
                        className="pl-7"
                        {...field}
                        onChange={e => field.onChange(parseFloat(e.target.value) || 0)}
                      />
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="method"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Payment Method</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {PAYMENT_METHODS.map(method => (
                        <SelectItem key={method.value} value={method.value}>
                          {method.label}
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
              name="reference"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Reference (optional)</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="e.g., Check #1234, VISA **** 4242"
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
                  <FormLabel>Notes (optional)</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Payment notes..."
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
              <Button type="submit">Record Payment</Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
