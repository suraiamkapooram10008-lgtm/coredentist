// ============================================
// CoreDent PMS - Invoice Card Component
// Summary card for an invoice
// ============================================

import React from 'react';
import { format } from 'date-fns';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  MoreVertical, 
  Eye, 
  CreditCard, 
  Download,
  Send,
  Trash2,
  User,
  Calendar
} from 'lucide-react';
import type { Invoice } from '@/types/billing';
import { STATUS_CONFIG } from '@/types/billing';
import { cn } from '@/lib/utils';

interface InvoiceCardProps {
  invoice: Invoice;
  onView: (invoice: Invoice) => void;
  onRecordPayment: (invoice: Invoice) => void;
  onDownload: (invoice: Invoice) => void;
  onSend?: (invoice: Invoice) => void;
  onDelete: (invoice: Invoice) => void;
}

export function InvoiceCard({
  invoice,
  onView,
  onRecordPayment,
  onDownload,
  onSend,
  onDelete,
}: InvoiceCardProps) {
  const statusConfig = STATUS_CONFIG[invoice.status];
  const canRecordPayment = ['draft', 'sent', 'partial', 'overdue'].includes(invoice.status);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm font-medium">
                {invoice.invoiceNumber}
              </span>
              <Badge className={cn('capitalize', statusConfig.color)}>
                {statusConfig.label}
              </Badge>
            </div>
            <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
              <User className="h-3.5 w-3.5" />
              <span>{invoice.patientName}</span>
            </div>
          </div>
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onView(invoice)}>
                <Eye className="h-4 w-4 mr-2" />
                View Details
              </DropdownMenuItem>
              {canRecordPayment && (
                <DropdownMenuItem onClick={() => onRecordPayment(invoice)}>
                  <CreditCard className="h-4 w-4 mr-2" />
                  Record Payment
                </DropdownMenuItem>
              )}
              <DropdownMenuItem onClick={() => onDownload(invoice)}>
                <Download className="h-4 w-4 mr-2" />
                Download Receipt
              </DropdownMenuItem>
              {onSend && invoice.status === 'draft' && (
                <DropdownMenuItem onClick={() => onSend(invoice)}>
                  <Send className="h-4 w-4 mr-2" />
                  Send to Patient
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => onDelete(invoice)}
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-3">
        {/* Amounts */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-muted-foreground">Total</p>
            <p className="font-semibold">{formatCurrency(invoice.total)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Balance</p>
            <p className={cn(
              'font-semibold',
              invoice.balance > 0 ? 'text-amber-600' : 'text-green-600'
            )}>
              {formatCurrency(invoice.balance)}
            </p>
          </div>
        </div>
        
        {/* Line items count */}
        <p className="text-sm text-muted-foreground">
          {invoice.lineItems.length} procedure{invoice.lineItems.length !== 1 ? 's' : ''}
        </p>
        
        {/* Dates */}
        <div className="flex items-center gap-1 text-xs text-muted-foreground pt-2 border-t">
          <Calendar className="h-3 w-3" />
          <span>Issued: {format(new Date(invoice.issueDate), 'MMM d, yyyy')}</span>
          <span className="mx-1">•</span>
          <span className={cn(
            invoice.status === 'overdue' && 'text-destructive font-medium'
          )}>
            Due: {format(new Date(invoice.dueDate), 'MMM d, yyyy')}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
