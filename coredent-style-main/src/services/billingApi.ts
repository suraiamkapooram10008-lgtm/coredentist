// ============================================
// CoreDent PMS - Billing API Service
// API calls for invoicing and payments
// ============================================

import type { 
  Invoice, 
  InvoiceStatus,
  InvoiceLineItem,
  BillingSummary,
  PaymentMethod 
} from '@/types/billing';
import { apiClient } from './api';

export const billingApi = {
  // Get all invoices
  async getInvoices(filters?: { 
    status?: InvoiceStatus; 
    patientId?: string;
    search?: string;
  }): Promise<Invoice[]> {
    const response = await apiClient.get<Invoice[]>('/invoices', filters as Record<string, unknown>);
    return response.success && response.data ? response.data : [];
  },

  // Get single invoice
  async getInvoice(invoiceId: string): Promise<Invoice | null> {
    const response = await apiClient.get<Invoice>(`/invoices/${invoiceId}`);
    return response.success ? response.data ?? null : null;
  },

  // Get billing summary
  async getSummary(): Promise<BillingSummary> {
    const response = await apiClient.get<BillingSummary>('/billing/summary');
    if (response.success && response.data) {
      return response.data;
    }
    return {
      totalOutstanding: 0,
      totalPaidToday: 0,
      totalPaidThisMonth: 0,
      overdueCount: 0,
      pendingCount: 0,
    };
  },

  // Create invoice
  async createInvoice(data: {
    patientId: string;
    patientName: string;
    patientEmail?: string;
    patientPhone?: string;
    lineItems: Omit<InvoiceLineItem, 'id' | 'total'>[];
    taxRate?: number;
    dueDate: string;
    notes?: string;
  }): Promise<Invoice> {
    const response = await apiClient.post<Invoice>('/invoices', data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to create invoice');
  },

  // Update invoice status
  async updateStatus(invoiceId: string, status: InvoiceStatus): Promise<Invoice> {
    const response = await apiClient.put<Invoice>(`/invoices/${invoiceId}/status`, { status });
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to update invoice status');
  },

  // Record payment
  async recordPayment(invoiceId: string, payment: {
    amount: number;
    method: PaymentMethod;
    reference?: string;
    notes?: string;
  }): Promise<Invoice> {
    const response = await apiClient.post<Invoice>(`/invoices/${invoiceId}/payments`, payment);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to record payment');
  },

  // Delete invoice
  async deleteInvoice(invoiceId: string): Promise<void> {
    await apiClient.delete<void>(`/invoices/${invoiceId}`);
  },

  // Generate receipt HTML
  generateReceiptHTML(invoice: Invoice): string {
    const formatCurrency = (amount: number) => 
      new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
    
    const lineItemsHTML = invoice.lineItems.map(item => `
      <tr>
        <td style="padding: 8px; border-bottom: 1px solid #eee;">
          <strong>${item.procedureCode}</strong><br>
          <span style="color: #666;">${item.description}</span>
          ${item.toothNumber ? `<br><small>Tooth #${item.toothNumber}</small>` : ''}
        </td>
        <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">${item.quantity}</td>
        <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">${formatCurrency(item.unitPrice)}</td>
        <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">${formatCurrency(item.discount)}</td>
        <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">${formatCurrency(item.total)}</td>
      </tr>
    `).join('');
    
    const paymentsHTML = invoice.payments.map(pay => `
      <tr>
        <td style="padding: 8px;">${pay.date}</td>
        <td style="padding: 8px;">${pay.method.replace('_', ' ')}</td>
        <td style="padding: 8px;">${pay.reference || '-'}</td>
        <td style="padding: 8px; text-align: right;">${formatCurrency(pay.amount)}</td>
      </tr>
    `).join('');

    return `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Receipt - ${invoice.invoiceNumber}</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
          .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 20px; }
          .invoice-info { display: flex; justify-content: space-between; margin-bottom: 30px; }
          table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
          th { background: #f5f5f5; padding: 10px; text-align: left; }
          .totals { text-align: right; }
          .totals td { padding: 5px 0; }
          .total-row { font-weight: bold; font-size: 1.1em; }
          .paid-stamp { color: green; font-size: 1.5em; font-weight: bold; text-align: center; margin: 20px 0; }
          @media print { body { padding: 0; } }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>CoreDent Dental Practice</h1>
          <p>123 Dental Street, Suite 100<br>City, State 12345<br>Phone: (555) 123-4567</p>
        </div>
        
        <div class="invoice-info">
          <div>
            <h3>Bill To:</h3>
            <p><strong>${invoice.patientName}</strong><br>
            ${invoice.patientEmail || ''}<br>
            ${invoice.patientPhone || ''}</p>
          </div>
          <div style="text-align: right;">
            <h3>Invoice #${invoice.invoiceNumber}</h3>
            <p>Issue Date: ${invoice.issueDate}<br>
            Due Date: ${invoice.dueDate}</p>
          </div>
        </div>
        
        <table>
          <thead>
            <tr>
              <th>Description</th>
              <th style="text-align: center;">Qty</th>
              <th style="text-align: right;">Price</th>
              <th style="text-align: right;">Discount</th>
              <th style="text-align: right;">Total</th>
            </tr>
          </thead>
          <tbody>
            ${lineItemsHTML}
          </tbody>
        </table>
        
        <table class="totals" style="width: 300px; margin-left: auto;">
          <tr><td>Subtotal:</td><td>${formatCurrency(invoice.subtotal)}</td></tr>
          ${invoice.discountTotal > 0 ? `<tr><td>Discounts:</td><td>-${formatCurrency(invoice.discountTotal)}</td></tr>` : ''}
          ${invoice.taxAmount > 0 ? `<tr><td>Tax (${invoice.taxRate}%):</td><td>${formatCurrency(invoice.taxAmount)}</td></tr>` : ''}
          <tr class="total-row" style="border-top: 2px solid #333;"><td>Total:</td><td>${formatCurrency(invoice.total)}</td></tr>
          <tr><td>Amount Paid:</td><td>${formatCurrency(invoice.amountPaid)}</td></tr>
          <tr class="total-row"><td>Balance Due:</td><td>${formatCurrency(invoice.balance)}</td></tr>
        </table>
        
        ${invoice.status === 'paid' ? '<div class="paid-stamp">✓ PAID IN FULL</div>' : ''}
        
        ${invoice.payments.length > 0 ? `
          <h3>Payment History</h3>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Method</th>
                <th>Reference</th>
                <th style="text-align: right;">Amount</th>
              </tr>
            </thead>
            <tbody>
              ${paymentsHTML}
            </tbody>
          </table>
        ` : ''}
        
        <p style="margin-top: 40px; text-align: center; color: #666;">
          Thank you for choosing CoreDent Dental Practice!
        </p>
      </body>
      </html>
    `;
  },
};
