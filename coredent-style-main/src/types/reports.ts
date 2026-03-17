// ============================================
// CoreDent PMS - Reports Types
// Types for analytics and reporting
// ============================================

export interface DateRange {
  from: Date;
  to: Date;
}

export interface AppointmentsSummary {
  total: number;
  completed: number;
  cancelled: number;
  noShow: number;
  scheduled: number;
  completionRate: number;
  noShowRate: number;
  byType: { type: string; count: number; color: string }[];
  byDay: { day: string; count: number }[];
}

export interface RevenueSummary {
  totalRevenue: number;
  totalCollected: number;
  totalOutstanding: number;
  averagePerVisit: number;
  byMonth: { month: string; revenue: number; collected: number }[];
  byProcedure: { procedure: string; revenue: number; count: number }[];
}

export interface TreatmentAcceptance {
  proposedPlans: number;
  acceptedPlans: number;
  completedPlans: number;
  acceptanceRate: number;
  completionRate: number;
  byMonth: { month: string; proposed: number; accepted: number }[];
}

export interface ChairUtilization {
  totalChairs: number;
  averageUtilization: number;
  peakHours: { hour: string; utilization: number }[];
  byChair: { chair: string; utilization: number; appointments: number }[];
  byDayOfWeek: { day: string; utilization: number }[];
}

export interface DashboardMetrics {
  appointments: AppointmentsSummary;
  revenue: RevenueSummary;
  treatmentAcceptance: TreatmentAcceptance;
  chairUtilization: ChairUtilization;
}

export type ReportType = 'appointments' | 'revenue' | 'treatment' | 'utilization';

export interface ExportOptions {
  format: 'csv' | 'pdf';
  reportType: ReportType;
  dateRange: DateRange;
}
