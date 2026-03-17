// ============================================
// CoreDent PMS - Settings Types
// Types for billing and practice preferences
// ============================================

export interface BillingPreferences {
  taxRate: number;
  taxLabel: string;
  enableTax: boolean;
  defaultPaymentTerms: number; // days
  invoicePrefix: string;
  invoiceStartNumber: number;
  currency: string;
  acceptedPaymentMethods: PaymentMethod[];
  receiptFooterText: string;
  lateFeeEnabled: boolean;
  lateFeePercentage: number;
  lateFeeGracePeriod: number; // days
  autoSendInvoices: boolean;
  autoSendReceipts: boolean;
}

export type PaymentMethod = 'cash' | 'check' | 'credit_card' | 'debit_card' | 'bank_transfer';

export const paymentMethodLabels: Record<PaymentMethod, string> = {
  cash: 'Cash',
  check: 'Check',
  credit_card: 'Credit Card',
  debit_card: 'Debit Card',
  bank_transfer: 'Bank Transfer',
};

export const defaultBillingPreferences: BillingPreferences = {
  taxRate: 0,
  taxLabel: 'Tax',
  enableTax: false,
  defaultPaymentTerms: 30,
  invoicePrefix: 'INV',
  invoiceStartNumber: 1001,
  currency: 'USD',
  acceptedPaymentMethods: ['cash', 'check', 'credit_card', 'debit_card'],
  receiptFooterText: 'Thank you for your payment!',
  lateFeeEnabled: false,
  lateFeePercentage: 1.5,
  lateFeeGracePeriod: 15,
  autoSendInvoices: true,
  autoSendReceipts: true,
};

export const currencyOptions = [
  { code: 'USD', label: 'US Dollar ($)', symbol: '$' },
  { code: 'EUR', label: 'Euro (€)', symbol: '€' },
  { code: 'GBP', label: 'British Pound (£)', symbol: '£' },
  { code: 'CAD', label: 'Canadian Dollar ($)', symbol: '$' },
  { code: 'AUD', label: 'Australian Dollar ($)', symbol: '$' },
];
