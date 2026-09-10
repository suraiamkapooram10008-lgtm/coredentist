import type { ApiResponse } from '@/types/api';
import { apiClient } from './api';

export interface EnterprisePracticeAnalytics {
  practice_id: string;
  practice_name: string;
  production: number;
  collections: number;
  new_patients: number;
  utilization: number;
}

export interface EnterpriseGroupAnalytics {
  group_id: string;
  period: {
    start: string;
    end: string;
  };
  consolidated: {
    production: number;
    collections: number;
    new_patients: number;
    avg_utilization: number;
  };
  by_location: EnterprisePracticeAnalytics[];
}

export interface EnterprisePractice {
  id: string;
  name: string;
  address_city?: string | null;
  address_state?: string | null;
}

export const enterpriseApi = {
  getGroupAnalytics: (params?: { start_date?: string; end_date?: string }): Promise<ApiResponse<EnterpriseGroupAnalytics>> =>
    apiClient.get<EnterpriseGroupAnalytics>('/enterprise/group/analytics', params),

  listGroupPractices: (params?: { page?: number; limit?: number }): Promise<ApiResponse<EnterprisePractice[]>> =>
    apiClient.get<EnterprisePractice[]>('/enterprise/group/practices', params),
};
