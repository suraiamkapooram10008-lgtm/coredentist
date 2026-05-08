/**
 * Payroll API Service
 */
import { apiClient } from './api';

export interface EmployeeCompensation {
  id: string;
  user_id: string;
  practice_id: string;
  pay_type: 'salary' | 'hourly' | 'contract';
  pay_rate: number;
  overtime_rate_multiplier: number;
  overtime_threshold_hours: number;
  commission_enabled: boolean;
  commission_structure_id?: string;
  effective_date: string;
  is_active: boolean;
  created_at: string;
}

export interface CommissionStructure {
  id: string;
  name: string;
  commission_type: string;
  rate_percentage?: number;
  tiers?: { min: number; max: number; rate: number }[];
  procedure_rates?: Record<string, number>;
  applies_to_roles?: string[];
  is_active: boolean;
}

export interface TimesheetEntry {
  id: string;
  user_id: string;
  work_date: string;
  clock_in: string;
  clock_out?: string;
  break_minutes: number;
  total_hours?: number;
  overtime_hours: number;
  status: 'pending' | 'approved' | 'rejected';
  notes?: string;
}

export interface PayrollPeriod {
  id: string;
  period_start: string;
  period_end: string;
  pay_date?: string;
  status: 'open' | 'processing' | 'closed';
  total_gross: number;
  total_commissions: number;
  total_overtime: number;
  processed_at?: string;
}

export interface PayrollEntry {
  id: string;
  user_id: string;
  regular_hours: number;
  overtime_hours: number;
  base_pay: number;
  overtime_pay: number;
  commission_amount: number;
  bonus: number;
  gross_pay: number;
  net_pay: number;
  total_production: number;
  total_collections: number;
  procedures_completed: number;
}

export interface ProductionSummary {
  user_id: string;
  user_name: string;
  role: string;
  total_production: number;
  total_collections: number;
  collection_rate: number;
  procedures_completed: number;
  avg_production_per_procedure: number;
}

const BASE = '/payroll';

export const payrollApi = {
  // Compensation
  listCompensation: async () => {
    const { data } = await apiClient.get(`${BASE}/compensation/`);
    return data;
  },
  createCompensation: async (d: any) => {
    const { data } = await apiClient.post(`${BASE}/compensation/`, d);
    return data;
  },

  // Commission Structures
  listCommissionStructures: async () => {
    const { data } = await apiClient.get(`${BASE}/commissions/structures/`);
    return data;
  },
  createCommissionStructure: async (d: any) => {
    const { data } = await apiClient.post(`${BASE}/commissions/structures/`, d);
    return data;
  },

  // Timesheets
  listTimesheets: async (params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    const { data } = await apiClient.get(`${BASE}/timesheets/${query}`);
    return data;
  },
  clockIn: async () => {
    const { data } = await apiClient.post(`${BASE}/timesheets/clock-in`);
    return data;
  },
  clockOut: async (breakMinutes = 0) => {
    const { data } = await apiClient.post(`${BASE}/timesheets/clock-out`, { break_minutes: breakMinutes });
    return data;
  },
  approveTimesheet: async (id: string) => {
    const { data } = await apiClient.post(`${BASE}/timesheets/${id}/approve`);
    return data;
  },

  // Payroll Periods
  listPeriods: async () => {
    const { data } = await apiClient.get(`${BASE}/periods/`);
    return data;
  },
  createPeriod: async (d: any) => {
    const { data } = await apiClient.post(`${BASE}/periods/`, d);
    return data;
  },
  processPeriod: async (id: string) => {
    const { data } = await apiClient.post(`${BASE}/periods/${id}/process`);
    return data;
  },
  getPeriodEntries: async (id: string) => {
    const { data } = await apiClient.get(`${BASE}/periods/${id}/entries`);
    return data;
  },

  // Production
  getProduction: async (startDate: string, endDate: string, userId?: string) => {
    const params: Record<string, string> = { start_date: startDate, end_date: endDate };
    if (userId) params.user_id = userId;
    const { data } = await apiClient.get(`${BASE}/production/?${new URLSearchParams(params)}`);
    return data;
  },
  getProductionSummary: async (startDate: string, endDate: string) => {
    const { data } = await apiClient.get(`${BASE}/production/summary?start_date=${startDate}&end_date=${endDate}`);
    return data;
  },

  // PTO
  getPTOBalances: async (userId?: string) => {
    const q = userId ? `?user_id=${userId}` : '';
    const { data } = await apiClient.get(`${BASE}/pto/balances${q}`);
    return data;
  },
  createPTORequest: async (d: any) => {
    const { data } = await apiClient.post(`${BASE}/pto/requests`, d);
    return data;
  },
  approvePTORequest: async (id: string, action: 'approve' | 'reject', reason?: string) => {
    const q = reason ? `&rejection_reason=${encodeURIComponent(reason)}` : '';
    const { data } = await apiClient.post(`${BASE}/pto/requests/${id}/approve?action=${action}${q}`);
    return data;
  },
};

export const PAY_TYPE_LABELS: Record<string, string> = {
  salary: 'Salaried', hourly: 'Hourly', contract: 'Contract',
};
