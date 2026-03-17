// ============================================
// CoreDent PMS - Billing Types
// Types for invoicing and payment tracking
// ============================================

export type InvoiceStatus = 'draft' | 'sent' | 'partial' | 'paid' | 'overdue' | 'cancelled';
export type PaymentMethod = 'cash' | 'credit_card' | 'debit_card' | 'check' | 'bank_transfer' | 'other';

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

export interface Payment {
  id: string;
  invoiceId: string;
  amount: number;
  method: PaymentMethod;
  reference?: string;
  date: string;
  receivedBy: string;
  notes?: string;
}

export interface Invoice {
  id: string;
  invoiceNumber: string;
  patientId: string;
  patientName: string;
  patientEmail?: string;
  patientPhone?: string;
  treatmentPlanId?: string;
  status: InvoiceStatus;
  lineItems: InvoiceLineItem[];
  subtotal: number;
  discountTotal: number;
  taxRate: number;
  taxAmount: number;
  total: number;
  amountPaid: number;
  balance: number;
  payments: Payment[];
  issueDate: string;
  dueDate: string;
  paidDate?: string;
  notes?: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface BillingSummary {
  totalOutstanding: number;
  totalPaidToday: number;
  totalPaidThisMonth: number;
  overdueCount: number;
  pendingCount: number;
}

export const STATUS_CONFIG: Record<InvoiceStatus, { label: string; color: string }> = {
  draft: { label: 'Draft', color: 'bg-slate-100 text-slate-700' },
  sent: { label: 'Sent', color: 'bg-blue-100 text-blue-700' },
  partial: { label: 'Partial', color: 'bg-amber-100 text-amber-700' },
  paid: { label: 'Paid', color: 'bg-green-100 text-green-700' },
  overdue: { label: 'Overdue', color: 'bg-red-100 text-red-700' },
  cancelled: { label: 'Cancelled', color: 'bg-gray-100 text-gray-500' },
};

export const PAYMENT_METHODS: { value: PaymentMethod; label: string }[] = [
  { value: 'cash', label: 'Cash' },
  { value: 'credit_card', label: 'Credit Card' },
  { value: 'debit_card', label: 'Debit Card' },
  { value: 'check', label: 'Check' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'other', label: 'Other' },
];

export function generateInvoiceNumber(): string {
  const date = new Date();
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
  return `INV-${year}${month}-${random}`;
}

export function calculateInvoiceTotals(
  lineItems: InvoiceLineItem[],
  taxRate: number = 0
): { subtotal: number; discountTotal: number; taxAmount: number; total: number } {
  const subtotal = lineItems.reduce((sum, item) => sum + (item.quantity * item.unitPrice), 0);
  const discountTotal = lineItems.reduce((sum, item) => sum + item.discount, 0);
  const taxableAmount = subtotal - discountTotal;
  const taxAmount = taxableAmount * (taxRate / 100);
  const total = taxableAmount + taxAmount;
  
  return { subtotal, discountTotal, taxAmount, total };
}
