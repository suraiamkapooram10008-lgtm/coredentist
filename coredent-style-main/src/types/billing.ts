// ============================================
// CoreDent PMS - Billing Types
// ============================================

export type InvoiceStatus = 'draft' | 'sent' | 'partial' | 'paid' | 'overdue' | 'void';

export type PaymentMethod = 'cash' | 'check' | 'credit_card' | 'debit_card' | 'bank_transfer';

export interface InvoiceLineItem {
  id: string;
  procedureCode: string;
  description: string;
  toothNumber?: number;
  quantity: number;
  unitPrice: number;
  discount: number;
  total: number;
}

export interface InvoicePayment {
  id: string;
  date: string;
  method: PaymentMethod;
  reference?: string;
  amount: number;
  notes?: string;
}

export interface Invoice {
  id: string;
  patientId: string;
  patientName: string;
  patientEmail?: string;
  patientPhone?: string;
  invoiceNumber: string;
  status: InvoiceStatus;
  lineItems: InvoiceLineItem[];
  subtotal: number;
  taxRate: number;
  taxAmount: number;
  discountTotal: number;
  total: number;
  amountPaid: number;
  balance: number;
  issueDate: string;
  dueDate: string;
  notes?: string;
  payments: InvoicePayment[];
  createdAt: string;
  updatedAt: string;
}

export interface BillingSummary {
  totalOutstanding: number;
  totalPaidToday: number;
  totalPaidThisMonth: number;
  overdueCount: number;
  pendingCount: number;
  pendingAmount?: number;
}
