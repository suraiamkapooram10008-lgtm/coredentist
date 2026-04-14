// ============================================
// CoreDent PMS - Reports API Service
// API calls for analytics and reporting
// ============================================

import type { 
  DateRange, 
  DashboardMetrics,
  ReportType
} from '@/types/reports';
import type { ApiResponse } from '@/types/api';
import { format } from 'date-fns';
import { apiClient } from './api';

export const reportsApi = {
  // Get full dashboard metrics
  async getDashboardMetrics(dateRange: DateRange): Promise<ApiResponse<DashboardMetrics>> {
    // Backend expects date strings in YYYY-MM-DD format, not ISO timestamps
    const fromDate = dateRange.from.toISOString().split('T')[0];
    const toDate = dateRange.to.toISOString().split('T')[0];
    
    const response = await apiClient.get<DashboardMetrics>('/reports/dashboard', {
      from: fromDate,
      to: toDate,
    });
    
    // Return the full ApiResponse, not just the data
    return response;
  },

  // Export report as CSV
  exportToCSV(reportType: ReportType, data: DashboardMetrics, dateRange: DateRange): string {
    const dateStr = `${format(dateRange.from, 'yyyy-MM-dd')}_to_${format(dateRange.to, 'yyyy-MM-dd')}`;
    let csv = '';

    switch (reportType) {
      case 'appointments':
        csv = 'Appointments Report\n';
        csv += `Date Range,${format(dateRange.from, 'MMM d, yyyy')} - ${format(dateRange.to, 'MMM d, yyyy')}\n\n`;
        csv += 'Metric,Value\n';
        csv += `Total Appointments,${data.appointments.total}\n`;
        csv += `Completed,${data.appointments.completed}\n`;
        csv += `Cancelled,${data.appointments.cancelled}\n`;
        csv += `No-Shows,${data.appointments.noShow}\n`;
        csv += `Completion Rate,${data.appointments.completionRate}%\n`;
        csv += `No-Show Rate,${data.appointments.noShowRate}%\n\n`;
        csv += 'By Type\nType,Count\n';
        data.appointments.byType.forEach(t => {
          csv += `${t.type},${t.count}\n`;
        });
        break;

      case 'revenue':
        csv = 'Revenue Report\n';
        csv += `Date Range,${format(dateRange.from, 'MMM d, yyyy')} - ${format(dateRange.to, 'MMM d, yyyy')}\n\n`;
        csv += 'Metric,Value\n';
        csv += `Total Revenue,$${data.revenue.totalRevenue.toLocaleString()}\n`;
        csv += `Total Collected,$${data.revenue.totalCollected.toLocaleString()}\n`;
        csv += `Outstanding,$${data.revenue.totalOutstanding.toLocaleString()}\n`;
        csv += `Avg Per Visit,$${data.revenue.averagePerVisit}\n\n`;
        csv += 'By Month\nMonth,Revenue,Collected\n';
        data.revenue.byMonth.forEach(m => {
          csv += `${m.month},$${m.revenue},$${m.collected}\n`;
        });
        break;

      case 'treatment':
        csv = 'Treatment Acceptance Report\n';
        csv += `Date Range,${format(dateRange.from, 'MMM d, yyyy')} - ${format(dateRange.to, 'MMM d, yyyy')}\n\n`;
        csv += 'Metric,Value\n';
        csv += `Proposed Plans,${data.treatmentAcceptance.proposedPlans}\n`;
        csv += `Accepted Plans,${data.treatmentAcceptance.acceptedPlans}\n`;
        csv += `Completed Plans,${data.treatmentAcceptance.completedPlans}\n`;
        csv += `Acceptance Rate,${data.treatmentAcceptance.acceptanceRate}%\n`;
        csv += `Completion Rate,${data.treatmentAcceptance.completionRate}%\n`;
        break;

      case 'utilization':
        csv = 'Chair Utilization Report\n';
        csv += `Date Range,${format(dateRange.from, 'MMM d, yyyy')} - ${format(dateRange.to, 'MMM d, yyyy')}\n\n`;
        csv += 'Metric,Value\n';
        csv += `Total Chairs,${data.chairUtilization.totalChairs}\n`;
        csv += `Average Utilization,${data.chairUtilization.averageUtilization}%\n\n`;
        csv += 'By Chair\nChair,Utilization,Appointments\n';
        data.chairUtilization.byChair.forEach(c => {
          csv += `${c.chair},${c.utilization}%,${c.appointments}\n`;
        });
        break;
    }

    return csv;
  },

  // Download CSV file
  downloadCSV(filename: string, content: string): void {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filename}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  },
};
