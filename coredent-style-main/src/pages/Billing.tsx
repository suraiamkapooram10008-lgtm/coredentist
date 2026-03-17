// ============================================
// CoreDent PMS - Billing Page
// Invoice management and payment tracking
// ============================================

import React, { useState, useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { 
  Plus, 
  Search, 
  FileText, 
  DollarSign,
  AlertTriangle,
  TrendingUp
} from 'lucide-react';
import { InvoiceCard } from '@/components/billing/InvoiceCard';
import { CreateInvoiceDialog } from '@/components/billing/CreateInvoiceDialog';
import { RecordPaymentDialog } from '@/components/billing/RecordPaymentDialog';
import { InvoiceDetails } from '@/components/billing/InvoiceDetails';
import { billingApi } from '@/services/billingApi';
import { triggerAutomation } from '@/services/automationApi';
import type { Invoice, InvoiceStatus, BillingSummary, PaymentMethod } from '@/types/billing';

type TabFilter = 'all' | 'pending' | 'paid' | 'overdue';

export default function Billing() {
  const { toast } = useToast();
  
  // State
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [summary, setSummary] = useState<BillingSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<TabFilter>('all');
  
  // Dialog states
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [paymentInvoice, setPaymentInvoice] = useState<Invoice | null>(null);
  const [viewingInvoice, setViewingInvoice] = useState<Invoice | null>(null);
  const [deletingInvoice, setDeletingInvoice] = useState<Invoice | null>(null);

  // Load data
  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const [invoicesData, summaryData] = await Promise.all([
          billingApi.getInvoices(),
          billingApi.getSummary(),
        ]);
        setInvoices(invoicesData);
        setSummary(summaryData);
      } catch (error) {
        toast({
          title: 'Error',
          description: 'Failed to load billing data',
          variant: 'destructive',
        });
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, [toast]);

  // Filter invoices
  const filteredInvoices = invoices.filter(invoice => {
    // Search filter
    const matchesSearch = 
      invoice.invoiceNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      invoice.patientName.toLowerCase().includes(searchQuery.toLowerCase());
    
    // Tab filter
    let matchesTab = true;
    if (activeTab === 'pending') {
      matchesTab = ['draft', 'sent', 'partial'].includes(invoice.status);
    } else if (activeTab === 'paid') {
      matchesTab = invoice.status === 'paid';
    } else if (activeTab === 'overdue') {
      matchesTab = invoice.status === 'overdue';
    }
    
    return matchesSearch && matchesTab;
  });

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  // Create invoice
  const handleCreateInvoice = async (data: {
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
  }) => {
    try {
      const newInvoice = await billingApi.createInvoice(data);
      setInvoices(prev => [newInvoice, ...prev]);
      
      // Refresh summary
      const summaryData = await billingApi.getSummary();
      setSummary(summaryData);
      
      toast({
        title: 'Invoice created',
        description: `Invoice ${newInvoice.invoiceNumber} has been created`,
      });

      // Trigger invoice_created automation
      triggerAutomation('invoice_created', {
        paymentId: '',
        invoiceId: newInvoice.id,
        patientName: data.patientName,
        patientEmail: data.patientEmail,
        amount: newInvoice.total,
        paymentMethod: '',
        clinicName: 'CoreDent Clinic',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create invoice',
        variant: 'destructive',
      });
    }
  };

  // Record payment
  const handleRecordPayment = async (data: {
    amount: number;
    method: PaymentMethod;
    reference?: string;
    notes?: string;
  }) => {
    if (!paymentInvoice) return;
    
    try {
      const updated = await billingApi.recordPayment(paymentInvoice.id, data);
      setInvoices(prev => prev.map(inv => inv.id === updated.id ? updated : inv));
      if (viewingInvoice?.id === updated.id) {
        setViewingInvoice(updated);
      }
      
      // Refresh summary
      const summaryData = await billingApi.getSummary();
      setSummary(summaryData);
      
      toast({
        title: 'Payment recorded',
        description: `${formatCurrency(data.amount)} payment recorded`,
      });

      // Trigger payment_received automation
      triggerAutomation('payment_received', {
        paymentId: crypto.randomUUID(),
        invoiceId: paymentInvoice.id,
        patientName: paymentInvoice.patientName,
        patientEmail: paymentInvoice.patientEmail,
        amount: data.amount,
        paymentMethod: data.method,
        clinicName: 'CoreDent Clinic',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to record payment',
        variant: 'destructive',
      });
    }
  };

  // Download receipt
  const handleDownload = (invoice: Invoice) => {
    const html = billingApi.generateReceiptHTML(invoice);
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `receipt-${invoice.invoiceNumber}.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    toast({
      title: 'Receipt downloaded',
      description: 'Open the file in a browser to print',
    });
  };

  // Send invoice
  const handleSend = async (invoice: Invoice) => {
    try {
      const updated = await billingApi.updateStatus(invoice.id, 'sent');
      setInvoices(prev => prev.map(inv => inv.id === updated.id ? updated : inv));
      
      toast({
        title: 'Invoice sent',
        description: 'Invoice status updated to Sent',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update invoice status',
        variant: 'destructive',
      });
    }
  };

  // Delete invoice
  const handleDelete = async () => {
    if (!deletingInvoice) return;
    
    try {
      await billingApi.deleteInvoice(deletingInvoice.id);
      setInvoices(prev => prev.filter(inv => inv.id !== deletingInvoice.id));
      if (viewingInvoice?.id === deletingInvoice.id) {
        setViewingInvoice(null);
      }
      
      // Refresh summary
      const summaryData = await billingApi.getSummary();
      setSummary(summaryData);
      
      setDeletingInvoice(null);
      toast({
        title: 'Invoice deleted',
        description: 'Invoice has been deleted',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete invoice',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Billing</h1>
          <p className="text-muted-foreground">
            Manage invoices and track payments
          </p>
        </div>
        
        <Button onClick={() => setIsCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Invoice
        </Button>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardContent className="py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-100">
                  <DollarSign className="h-5 w-5 text-amber-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Outstanding</p>
                  <p className="text-xl font-bold">{formatCurrency(summary.totalOutstanding)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100">
                  <TrendingUp className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">This Month</p>
                  <p className="text-xl font-bold">{formatCurrency(summary.totalPaidThisMonth)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100">
                  <FileText className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Pending</p>
                  <p className="text-xl font-bold">{summary.pendingCount}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-100">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Overdue</p>
                  <p className="text-xl font-bold">{summary.overdueCount}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Search and filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search invoices..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabFilter)}>
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="pending">Pending</TabsTrigger>
            <TabsTrigger value="paid">Paid</TabsTrigger>
            <TabsTrigger value="overdue">Overdue</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Invoice grid */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map(i => (
            <Skeleton key={i} className="h-[200px] rounded-xl" />
          ))}
        </div>
      ) : filteredInvoices.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 mx-auto text-muted-foreground/50" />
          <h3 className="mt-4 text-lg font-medium">No invoices found</h3>
          <p className="text-muted-foreground mt-1">
            {searchQuery
              ? 'Try adjusting your search terms'
              : 'Create a new invoice to get started'}
          </p>
          {!searchQuery && (
            <Button className="mt-4" onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Invoice
            </Button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredInvoices.map(invoice => (
            <InvoiceCard
              key={invoice.id}
              invoice={invoice}
              onView={setViewingInvoice}
              onRecordPayment={setPaymentInvoice}
              onDownload={handleDownload}
              onSend={handleSend}
              onDelete={setDeletingInvoice}
            />
          ))}
        </div>
      )}

      {/* Dialogs */}
      <CreateInvoiceDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
        onSubmit={handleCreateInvoice}
      />

      <RecordPaymentDialog
        open={!!paymentInvoice}
        onOpenChange={(open) => !open && setPaymentInvoice(null)}
        invoice={paymentInvoice}
        onSubmit={handleRecordPayment}
      />

      <InvoiceDetails
        open={!!viewingInvoice}
        onOpenChange={(open) => !open && setViewingInvoice(null)}
        invoice={viewingInvoice}
        onRecordPayment={() => {
          setPaymentInvoice(viewingInvoice);
        }}
        onDownload={() => viewingInvoice && handleDownload(viewingInvoice)}
        onSend={() => viewingInvoice && handleSend(viewingInvoice)}
      />

      <AlertDialog open={!!deletingInvoice} onOpenChange={(open) => !open && setDeletingInvoice(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Invoice?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete invoice {deletingInvoice?.invoiceNumber}. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
