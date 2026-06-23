import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
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
import { Plus, Trash2 } from 'lucide-react';
import { patientsApi } from '@/services/api';

interface LineItemInput {
  procedureCode: string;
  description: string;
  toothNumber?: number;
  quantity: number;
  unitPrice: number;
  discount: number;
}

interface CreateInvoiceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: {
    patientId: string;
    patientName: string;
    patientEmail?: string;
    patientPhone?: string;
    lineItems: LineItemInput[];
    dueDate: string;
    notes?: string;
  }) => Promise<void>;
}

export function CreateInvoiceDialog({
  open,
  onOpenChange,
  onSubmit,
}: CreateInvoiceDialogProps) {
  // Query patients
  const { data: patientsResponse } = useQuery({
    queryKey: ['patients', 'list-simple'],
    queryFn: () => patientsApi.list({ limit: 100 }),
    enabled: open,
  });

  const patients = patientsResponse?.success && patientsResponse.data?.data
    ? patientsResponse.data.data
    : [];

  // Form State
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [dueDate, setDueDate] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lineItems, setLineItems] = useState<LineItemInput[]>([
    { procedureCode: 'D0120', description: 'Periodic Oral Evaluation', quantity: 1, unitPrice: 85, discount: 0 },
  ]);

  // Set default due date (30 days from now)
  useEffect(() => {
    if (open) {
      const date = new Date();
      date.setDate(date.getDate() + 30);
      setDueDate(date.toISOString().split('T')[0]);
      setSelectedPatientId('');
      setNotes('');
      setLineItems([
        { procedureCode: 'D0120', description: 'Periodic Oral Evaluation', quantity: 1, unitPrice: 85, discount: 0 },
      ]);
    }
  }, [open]);

  // Calculations
  const subtotal = lineItems.reduce((acc, item) => acc + (item.quantity * item.unitPrice), 0);
  const discountTotal = lineItems.reduce((acc, item) => acc + (item.discount || 0), 0);
  const taxRate = 5; // 5% flat practice tax
  const taxAmount = Math.max(0, (subtotal - discountTotal) * (taxRate / 100));
  const total = Math.max(0, subtotal - discountTotal + taxAmount);

  const handleAddLineItem = () => {
    setLineItems([
      ...lineItems,
      { procedureCode: '', description: '', quantity: 1, unitPrice: 0, discount: 0 },
    ]);
  };

  const handleRemoveLineItem = (index: number) => {
    if (lineItems.length === 1) return;
    setLineItems(lineItems.filter((_, i) => i !== index));
  };

  const handleLineItemChange = (index: number, field: keyof LineItemInput, value: any) => {
    const updated = [...lineItems];
    if (field === 'quantity' || field === 'unitPrice' || field === 'discount' || field === 'toothNumber') {
      updated[index] = {
        ...updated[index],
        [field]: value === '' ? 0 : Number(value),
      };
    } else {
      updated[index] = {
        ...updated[index],
        [field]: value,
      };
    }
    setLineItems(updated);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPatientId) return;

    const patient = patients.find(p => p.id === selectedPatientId);
    if (!patient) return;

    setIsSubmitting(true);
    try {
      await onSubmit({
        patientId: patient.id,
        patientName: `${patient.firstName} ${patient.lastName}`,
        patientEmail: patient.email,
        patientPhone: patient.phone,
        lineItems,
        dueDate,
        notes,
      });
      onOpenChange(false);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto bg-card/95 border border-border backdrop-blur-md text-foreground">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold">Create Invoice</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleFormSubmit} className="space-y-6">
          {/* Patient and Due Date */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="patientSelect">Patient</Label>
              <Select value={selectedPatientId} onValueChange={setSelectedPatientId} required>
                <SelectTrigger id="patientSelect" className="bg-background/60 border-border">
                  <SelectValue placeholder="Select patient..." />
                </SelectTrigger>
                <SelectContent className="bg-card border-border">
                  {patients.map(p => (
                    <SelectItem key={p.id} value={p.id} className="cursor-pointer">
                      {p.firstName} {p.lastName} ({p.email || 'No email'})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="dueDate">Due Date</Label>
              <Input
                type="date"
                id="dueDate"
                value={dueDate}
                onChange={e => setDueDate(e.target.value)}
                className="bg-background/60 border-border"
                required
              />
            </div>
          </div>

          {/* Line Items */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-sm font-semibold">Procedures / Items</Label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleAddLineItem}
                className="h-8 border-dashed border-primary/40 text-primary hover:bg-primary/5 hover:border-primary"
              >
                <Plus className="h-4 w-4 mr-1" /> Add Item
              </Button>
            </div>

            <div className="space-y-3 border border-border/40 rounded-xl p-4 bg-accent/10">
              {lineItems.map((item, index) => (
                <div key={index} className="grid grid-cols-12 gap-2 items-end border-b border-border/20 pb-3 last:border-0 last:pb-0">
                  <div className="col-span-2">
                    <Label className="text-[10px] text-muted-foreground uppercase tracking-wide">Code</Label>
                    <Input
                      placeholder="e.g. D1110"
                      value={item.procedureCode}
                      onChange={e => handleLineItemChange(index, 'procedureCode', e.target.value)}
                      className="h-9 bg-background/80 border-border text-xs"
                      required
                    />
                  </div>

                  <div className="col-span-3">
                    <Label className="text-[10px] text-muted-foreground uppercase tracking-wide">Description</Label>
                    <Input
                      placeholder="Prophylaxis..."
                      value={item.description}
                      onChange={e => handleLineItemChange(index, 'description', e.target.value)}
                      className="h-9 bg-background/80 border-border text-xs"
                      required
                    />
                  </div>

                  <div className="col-span-1">
                    <Label className="text-[10px] text-muted-foreground uppercase tracking-wide">Tooth</Label>
                    <Input
                      type="number"
                      placeholder="-"
                      value={item.toothNumber || ''}
                      onChange={e => handleLineItemChange(index, 'toothNumber', e.target.value)}
                      className="h-9 bg-background/80 border-border text-xs text-center"
                    />
                  </div>

                  <div className="col-span-1.5 col-start-8 col-span-1">
                    <Label className="text-[10px] text-muted-foreground uppercase tracking-wide text-center block">Qty</Label>
                    <Input
                      type="number"
                      min="1"
                      value={item.quantity}
                      onChange={e => handleLineItemChange(index, 'quantity', e.target.value)}
                      className="h-9 bg-background/80 border-border text-xs text-center"
                      required
                    />
                  </div>

                  <div className="col-span-2">
                    <Label className="text-[10px] text-muted-foreground uppercase tracking-wide text-right block">Price ($)</Label>
                    <Input
                      type="number"
                      min="0"
                      step="0.01"
                      value={item.unitPrice}
                      onChange={e => handleLineItemChange(index, 'unitPrice', e.target.value)}
                      className="h-9 bg-background/80 border-border text-xs text-right"
                      required
                    />
                  </div>

                  <div className="col-span-2">
                    <Label className="text-[10px] text-muted-foreground uppercase tracking-wide text-right block">Disc ($)</Label>
                    <Input
                      type="number"
                      min="0"
                      step="0.01"
                      value={item.discount}
                      onChange={e => handleLineItemChange(index, 'discount', e.target.value)}
                      className="h-9 bg-background/80 border-border text-xs text-right"
                    />
                  </div>

                  <div className="col-span-1 flex justify-center pb-1">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => handleRemoveLineItem(index)}
                      disabled={lineItems.length === 1}
                      className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Notes & Summary breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div className="space-y-2">
              <Label htmlFor="notes">Invoice Notes / Memo</Label>
              <Textarea
                id="notes"
                placeholder="Add special instructions, payment guidelines, or treatment notes..."
                value={notes}
                onChange={e => setNotes(e.target.value)}
                className="h-32 bg-background/60 border-border"
              />
            </div>

            <div className="rounded-xl border border-border/60 bg-accent/5 p-4 space-y-3 text-sm">
              <h4 className="font-semibold text-foreground border-b border-border pb-2">Calculation Summary</h4>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Subtotal</span>
                <span className="font-mono">${subtotal.toFixed(2)}</span>
              </div>
              {discountTotal > 0 && (
                <div className="flex justify-between text-emerald-500 font-medium">
                  <span>Discounts</span>
                  <span className="font-mono">-${discountTotal.toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between text-muted-foreground">
                <span>Tax ({taxRate}%)</span>
                <span className="font-mono">${taxAmount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between font-bold text-base border-t border-border pt-2 text-foreground">
                <span>Total Due</span>
                <span className="font-mono text-primary">${total.toFixed(2)}</span>
              </div>
            </div>
          </div>

          <DialogFooter className="border-t border-border/50 pt-4">
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
              disabled={isSubmitting || !selectedPatientId}
              className="bg-primary hover:bg-primary/90 text-primary-foreground font-semibold px-6"
            >
              {isSubmitting ? 'Creating...' : 'Create Invoice'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
