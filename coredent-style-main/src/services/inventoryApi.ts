/**
 * Inventory & Vendor API Service
 */
import { apiClient } from './api';

export interface Supplier {
  id: string;
  name: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  is_active: boolean;
}

export interface VendorContract {
  id: string;
  supplier_id: string;
  contract_number?: string;
  start_date: string;
  end_date: string;
  discount_percentage?: number;
  minimum_order_value?: number;
  shipping_terms?: string;
  is_active: boolean;
  supplier?: Supplier;
}

export interface ReorderRule {
  id: string;
  item_id: string;
  supplier_id?: string;
  trigger_quantity: number;
  reorder_quantity: number;
  auto_approve: boolean;
  is_active: boolean;
}

export interface VendorInvoice {
  id: string;
  supplier_id: string;
  purchase_order_id?: string;
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  amount_due: number;
  amount_paid: number;
  status: string;
}

const BASE = '/inventory';

export const inventoryApi = {
  // Original Inventory Endpoints...
  listItems: async (params?: Record<string, any>) => {
    const q = params ? '?' + new URLSearchParams(params).toString() : '';
    const { data } = await apiClient.get(`${BASE}/items/${q}`);
    return data;
  },
  
  // Suppliers
  listSuppliers: async () => {
    const { data } = await apiClient.get(`${BASE}/suppliers/`);
    return data;
  },
  createSupplier: async (payload: any) => {
    const { data } = await apiClient.post(`${BASE}/suppliers/`, payload);
    return data;
  },
  
  // Contracts
  listContracts: async () => {
    const { data } = await apiClient.get(`${BASE}/suppliers/contracts/`);
    return data;
  },
  createContract: async (payload: any) => {
    const { data } = await apiClient.post(`${BASE}/suppliers/contracts/`, payload);
    return data;
  },
  
  // Invoices
  listInvoices: async () => {
    const { data } = await apiClient.get(`${BASE}/suppliers/invoices/`);
    return data;
  },
  createInvoice: async (payload: any) => {
    const { data } = await apiClient.post(`${BASE}/suppliers/invoices/`, payload);
    return data;
  },
  
  // Reorder Rules
  listRules: async () => {
    const { data } = await apiClient.get(`${BASE}/suppliers/rules/`);
    return data;
  },
  createRule: async (payload: any) => {
    const { data } = await apiClient.post(`${BASE}/suppliers/rules/`, payload);
    return data;
  },
  
  triggerReorderCheck: async () => {
    const { data } = await apiClient.post(`${BASE}/suppliers/reorder-check`);
    return data;
  }
};
