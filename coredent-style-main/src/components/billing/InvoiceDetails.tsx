// ============================================
// CoreDent PMS - Invoice Details Sheet
// Full view of an invoice with payment history
// ============================================

import React from 'react';
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { 
  CreditCard, 
  Download, 
  Send, 
  User, 
  Mail, 
  Phone,
  Calendar,
  CheckCircle2,
  Clock
} from 'lucide-react';
import type { Invoice } from '@/types/billing';
import { STATUS_CONFIG } from '@/types/billing';
import { cn } from '@/lib/utils';

interface InvoiceDetailsProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  invoice: Invoice | null;
  onRecordPayment: () => void;
  onDownload: () => void;
  onSend?: () => void;
}

export function InvoiceDetails({
  open,
  onOpenChange,
  invoice,
  onRecordPayment,
  onDownload,
  onSend,
}: InvoiceDetailsProps) {
  if (!invoice) return null;

  const statusConfig = STATUS_CONFIG[invoice.status];
  const canRecordPayment = ['draft', 'sent', 'partial', 'overdue'].includes(invoice.status);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-2xl overflow-hidden flex flex-col">
        <SheetHeader className="flex-shrink-0">
          <div className="flex items-start justify-between gap-4 pr-8">
            <div className="space-y-1">
              <SheetTitle className="font-mono">{invoice.invoiceNumber}</SheetTitle>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <User className="h-4 w-4" />
                <span>{invoice.patientName}</span>
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
                  <p className="text-lg font-bold">{formatCurrency(invoice.total)}</p>
                  <p className="text-xs text-muted-foreground">Total</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="py-3 px-4 text-center">
                  <p className="text-lg font-bold text-green-600">
                    {formatCurrency(invoice.amountPaid)}
                  </p>
                  <p className="text-xs text-muted-foreground">Paid</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="py-3 px-4 text-center">
                  <p className={cn(
                    'text-lg font-bold',
                    invoice.balance > 0 ? 'text-amber-600' : 'text-green-600'
                  )}>
                    {formatCurrency(invoice.balance)}
                  </p>
                  <p className="text-xs text-muted-foreground">Balance</p>
                </CardContent>
              </Card>
            </div>

            {/* Patient contact */}
            <div className="flex flex-wrap gap-4 text-sm">
              {invoice.patientEmail && (
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <Mail className="h-4 w-4" />
                  {invoice.patientEmail}
                </div>
              )}
              {invoice.patientPhone && (
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <Phone className="h-4 w-4" />
                  {invoice.patientPhone}
                </div>
              )}
            </div>

            {/* Dates */}
            <div className="flex flex-wrap gap-4 text-sm">
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <Calendar className="h-4 w-4" />
                Issued: {format(new Date(invoice.issueDate), 'MMM d, yyyy')}
              </div>
              <div className={cn(
                'flex items-center gap-1.5',
                invoice.status === 'overdue' ? 'text-destructive' : 'text-muted-foreground'
              )}>
                <Clock className="h-4 w-4" />
                Due: {format(new Date(invoice.dueDate), 'MMM d, yyyy')}
              </div>
              {invoice.paidDate && (
                <div className="flex items-center gap-1.5 text-green-600">
                  <CheckCircle2 className="h-4 w-4" />
                  Paid: {format(new Date(invoice.paidDate), 'MMM d, yyyy')}
                </div>
              )}
            </div>

            <Separator />

            {/* Actions */}
            <div className="flex items-center gap-2">
              {canRecordPayment && (
                <Button onClick={onRecordPayment}>
                  <CreditCard className="h-4 w-4 mr-2" />
                  Record Payment
                </Button>
              )}
              <Button variant="outline" onClick={onDownload}>
                <Download className="h-4 w-4 mr-2" />
                Download Receipt
              </Button>
              {onSend && invoice.status === 'draft' && (
                <Button variant="outline" onClick={onSend}>
                  <Send className="h-4 w-4 mr-2" />
                  Send
                </Button>
              )}
            </div>

            {/* Line items */}
            <div>
              <h4 className="text-sm font-medium mb-3">Line Items</h4>
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-center w-16">Qty</TableHead>
                      <TableHead className="text-right w-24">Price</TableHead>
                      <TableHead className="text-right w-24">Discount</TableHead>
                      <TableHead className="text-right w-24">Total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invoice.lineItems.map(item => (
                      <TableRow key={item.id}>
                        <TableCell>
                          <div>
                            <span className="font-mono text-xs text-muted-foreground mr-2">
                              {item.procedureCode}
                            </span>
                            {item.description}
                            {item.toothNumber && (
                              <Badge variant="secondary" className="ml-2 text-xs">
                                Tooth #{item.toothNumber}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-center">{item.quantity}</TableCell>
                        <TableCell className="text-right">{formatCurrency(item.unitPrice)}</TableCell>
                        <TableCell className="text-right">
                          {item.discount > 0 ? `-${formatCurrency(item.discount)}` : '-'}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(item.total)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>

            {/* Totals */}
            <div className="bg-muted/50 p-4 rounded-lg space-y-1 text-sm">
              <div className="flex justify-between">
                <span>Subtotal:</span>
                <span>{formatCurrency(invoice.subtotal)}</span>
              </div>
              {invoice.discountTotal > 0 && (
                <div className="flex justify-between text-green-600">
                  <span>Discounts:</span>
                  <span>-{formatCurrency(invoice.discountTotal)}</span>
                </div>
              )}
              {invoice.taxAmount > 0 && (
                <div className="flex justify-between">
                  <span>Tax ({invoice.taxRate}%):</span>
                  <span>{formatCurrency(invoice.taxAmount)}</span>
                </div>
              )}
              <Separator className="my-2" />
              <div className="flex justify-between font-semibold text-base">
                <span>Total:</span>
                <span>{formatCurrency(invoice.total)}</span>
              </div>
              <div className="flex justify-between text-green-600">
                <span>Amount Paid:</span>
                <span>{formatCurrency(invoice.amountPaid)}</span>
              </div>
              <div className={cn(
                'flex justify-between font-semibold',
                invoice.balance > 0 ? 'text-amber-600' : 'text-green-600'
              )}>
                <span>Balance Due:</span>
                <span>{formatCurrency(invoice.balance)}</span>
              </div>
            </div>

            {/* Payment history */}
            {invoice.payments.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-3">Payment History</h4>
                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Date</TableHead>
                        <TableHead>Method</TableHead>
                        <TableHead>Reference</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {invoice.payments.map(payment => (
                        <TableRow key={payment.id}>
                          <TableCell>
                            {format(new Date(payment.date), 'MMM d, yyyy')}
                          </TableCell>
                          <TableCell className="capitalize">
                            {payment.method.replace('_', ' ')}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {payment.reference || '-'}
                          </TableCell>
                          <TableCell className="text-right font-medium text-green-600">
                            {formatCurrency(payment.amount)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}

            {/* Notes */}
            {invoice.notes && (
              <div>
                <h4 className="text-sm font-medium mb-2">Notes</h4>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {invoice.notes}
                </p>
              </div>
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
