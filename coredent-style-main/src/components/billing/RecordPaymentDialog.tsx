import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  CreditCard,
  Banknote,
  ClipboardList,
  FileCheck2,
  Receipt
} from 'lucide-react';
import type { Invoice, PaymentMethod } from '@/types/billing';

interface RecordPaymentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  invoice: Invoice | null;
  onSubmit: (data: {
    amount: number;
    method: PaymentMethod;
    reference?: string;
    notes?: string;
  }) => Promise<void>;
}

export function RecordPaymentDialog({
  open,
  onOpenChange,
  invoice,
  onSubmit,
}: RecordPaymentDialogProps) {
  const [amount, setAmount] = useState<number>(0);
  const [method, setMethod] = useState<PaymentMethod>('credit_card');
  const [reference, setReference] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Set default fields when invoice changes
  useEffect(() => {
    if (open && invoice) {
      setAmount(invoice.balance);
      setMethod('credit_card');
      setReference('');
      setNotes('');
    }
  }, [open, invoice]);

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!invoice || amount <= 0) return;

    setIsSubmitting(true);
    try {
      await onSubmit({
        amount,
        method,
        reference: reference || undefined,
        notes: notes || undefined,
      });
      onOpenChange(false);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(val);
  };

  if (!invoice) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md bg-card/95 border border-border backdrop-blur-md text-foreground">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold flex items-center gap-2">
            <Receipt className="h-5 w-5 text-primary" />
            Record Payment
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleFormSubmit} className="space-y-5">
          {/* Quick Invoice Details */}
          <div className="rounded-xl border border-border bg-accent/20 p-4 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Invoice Number:</span>
              <span className="font-semibold font-mono text-foreground">{invoice.invoiceNumber}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Patient Name:</span>
              <span className="font-semibold text-foreground">{invoice.patientName}</span>
            </div>
            <div className="flex justify-between border-t border-border/50 pt-2 text-sm">
              <span className="text-muted-foreground">Remaining Balance:</span>
              <span className="font-bold text-rose-500">{formatCurrency(invoice.balance)}</span>
            </div>
          </div>

          {/* Payment Amount */}
          <div className="space-y-2">
            <Label htmlFor="payAmount" className="text-sm font-semibold">Payment Amount ($)</Label>
            <div className="relative">
              <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground font-semibold">$</div>
              <Input
                type="number"
                id="payAmount"
                min="0.01"
                max={invoice.balance}
                step="0.01"
                value={amount || ''}
                onChange={e => setAmount(Number(e.target.value))}
                className="pl-7 bg-background/60 border-border text-lg font-mono font-semibold text-foreground"
                required
              />
              <Button 
                type="button" 
                variant="ghost" 
                size="sm"
                onClick={() => setAmount(invoice.balance)}
                className="absolute right-1 top-1/2 -translate-y-1/2 h-8 text-xs text-primary hover:bg-primary/10"
              >
                Pay Full
              </Button>
            </div>
          </div>

          {/* Payment Method */}
          <div className="space-y-2">
            <Label htmlFor="payMethod">Payment Method</Label>
            <Select value={method} onValueChange={(val) => setMethod(val as PaymentMethod)}>
              <SelectTrigger id="payMethod" className="bg-background/60 border-border">
                <SelectValue placeholder="Select method..." />
              </SelectTrigger>
              <SelectContent className="bg-card border-border">
                <SelectItem value="credit_card" className="cursor-pointer">
                  <span className="flex items-center gap-2">
                    <CreditCard className="h-4 w-4 text-primary" /> Credit Card
                  </span>
                </SelectItem>
                <SelectItem value="cash" className="cursor-pointer">
                  <span className="flex items-center gap-2">
                    <Banknote className="h-4 w-4 text-emerald-500" /> Cash
                  </span>
                </SelectItem>
                <SelectItem value="check" className="cursor-pointer">
                  <span className="flex items-center gap-2">
                    <ClipboardList className="h-4 w-4 text-amber-500" /> Check
                  </span>
                </SelectItem>
                <SelectItem value="debit_card" className="cursor-pointer">
                  <span className="flex items-center gap-2">
                    <CreditCard className="h-4 w-4 text-sky-500" /> Debit Card
                  </span>
                </SelectItem>
                <SelectItem value="bank_transfer" className="cursor-pointer">
                  <span className="flex items-center gap-2">
                    <FileCheck2 className="h-4 w-4 text-purple-500" /> Bank Transfer
                  </span>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Reference */}
          <div className="space-y-2">
            <Label htmlFor="reference">Reference / Check / Auth #</Label>
            <Input
              placeholder="e.g. Check number, CC auth code, Tx ID"
              id="reference"
              value={reference}
              onChange={e => setReference(e.target.value)}
              className="bg-background/60 border-border"
            />
          </div>

          {/* Memo / Notes */}
          <div className="space-y-2">
            <Label htmlFor="payNotes">Payment Notes</Label>
            <Textarea
              placeholder="Optional notes or memos about this payment..."
              id="payNotes"
              value={notes}
              onChange={e => setNotes(e.target.value)}
              className="h-20 bg-background/60 border-border resize-none"
            />
          </div>

          <DialogFooter className="pt-2 border-t border-border/50">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="border-border bg-background hover:bg-accent text-foreground"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting || amount <= 0}
              className="bg-primary hover:bg-primary/90 text-primary-foreground font-semibold px-5"
            >
              {isSubmitting ? 'Recording...' : 'Record Payment'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
