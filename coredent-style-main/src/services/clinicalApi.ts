/**
 * Clinical API Service for Visual Dental Charting & Perio
 */
import { apiClient } from './api';

export interface ToothCondition {
  id: string;
  patient_id: string;
  tooth_number: string;
  surface?: string;
  condition_type: string;
  status: 'existing' | 'planned' | 'completed';
  severity?: string;
  material?: string;
  notes?: string;
  noted_date?: string;
  provider_id?: string;
}

export interface ChartingEntry {
  id: string;
  tooth_number?: string;
  entry_type: string;
  data: Record<string, any>;
  created_at: string;
  provider_id?: string;
}

export interface DentalChartData {
  chart_id: string;
  base_data: Record<string, any>;
  conditions: ToothCondition[];
}

export interface ChartingSymbol {
  id: string;
  name: string;
  symbol_type?: string;
  category?: string;
  svg_data?: string;
  color?: string;
  is_active: boolean;
}

const BASE = '/clinical';

export const clinicalApi = {
  // Charting
  getPatientChart: async (patientId: string): Promise<DentalChartData> => {
    const { data } = await apiClient.get(`${BASE}/chart/${patientId}`);
    return data;
  },
  
  addCondition: async (patientId: string, condition: Partial<ToothCondition>) => {
    const { data } = await apiClient.post(`${BASE}/chart/${patientId}/conditions`, condition);
    return data;
  },
  
  removeCondition: async (patientId: string, conditionId: string) => {
    const { data } = await apiClient.delete(`${BASE}/chart/${patientId}/conditions/${conditionId}`);
    return data;
  },
  
  getChartHistory: async (patientId: string): Promise<{ history: ChartingEntry[] }> => {
    const { data } = await apiClient.get(`${BASE}/chart/${patientId}/history`);
    return data;
  },
  
  // Symbols
  getSymbols: async (): Promise<{ symbols: ChartingSymbol[] }> => {
    const { data } = await apiClient.get(`${BASE}/chart/symbols/`);
    return data;
  },
  
  createSymbol: async (symbol: Partial<ChartingSymbol>) => {
    const { data } = await apiClient.post(`${BASE}/chart/symbols/`, symbol);
    return data;
  },
  
  // Perio
  listPerioCharts: async (patientId?: string) => {
    const q = patientId ? `?patient_id=${patientId}` : '';
    const { data } = await apiClient.get(`${BASE}/perio/${q}`);
    return data;
  },
  
  createPerioChart: async (chartData: any) => {
    const { data } = await apiClient.post(`${BASE}/perio/`, chartData);
    return data;
  }
};
