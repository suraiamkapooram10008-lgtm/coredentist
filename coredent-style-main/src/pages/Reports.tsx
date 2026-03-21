// ============================================
// CoreDent PMS - Reports Page
// Analytics dashboard for clinic owners
// ============================================

import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Calendar } from '@/components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { 
  Download, 
  Calendar as CalendarIcon,
  Users,
  DollarSign,
  TrendingUp,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle
} from 'lucide-react';

// Components & Hooks
import { MetricCard } from '@/components/reports/MetricCard';
import { reportsApi } from '@/services/reportsApi';
import { useApiRequest } from '@/hooks/useApiRequest';
import { useDateRange } from '@/hooks/useDateRange';
import { cn } from '@/lib/utils';
import type { ReportType } from '@/types/reports';

// Extracted Charts
import { RevenueChart } from '@/components/reports/charts/RevenueChart';
import { AppointmentPieChart } from '@/components/reports/charts/AppointmentPieChart';
import { DailyAppointmentsChart } from '@/components/reports/charts/DailyAppointmentsChart';
import { MonthlyRevenueChart } from '@/components/reports/charts/MonthlyRevenueChart';
import { UtilizationCharts } from '@/components/reports/charts/UtilizationCharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const COLORS = [
  'hsl(var(--chart-1))',
  'hsl(var(--chart-2))',
  'hsl(var(--chart-3))',
  'hsl(var(--chart-4))',
  'hsl(var(--chart-5))',
  'hsl(var(--muted-foreground))',
];

export default function Reports() {
  const { 
    dateRange, 
    selectedPreset, 
    handlePresetChange, 
    setCustomRange, 
    PRESET_RANGES 
  } = useDateRange('last30days');

  const {
    data: metrics,
    isLoading,
    execute: loadMetrics
  } = useApiRequest(reportsApi.getDashboardMetrics, {
    errorMessage: 'Failed to load reports data'
  });

  const [activeTab, setActiveTab] = useState('overview');

  // effect:audited — Load metrics when date range changes
  useEffect(() => {
    loadMetrics(dateRange);
  }, [dateRange, loadMetrics]);

  const handleExport = (reportType: ReportType) => {
    if (!metrics) return;
    const csv = reportsApi.exportToCSV(reportType, metrics, dateRange);
    const filename = `${reportType}-report-${format(dateRange.from, 'yyyy-MM-dd')}`;
    reportsApi.downloadCSV(filename, csv);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Reports</h1>
          <p className="text-muted-foreground">Analytics and performance metrics</p>
        </div>
        
        <div className="flex items-center gap-2">
          <Select value={selectedPreset} onValueChange={(v) => handlePresetChange(v as any)}>
            <SelectTrigger className="w-[160px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PRESET_RANGES.map(range => (
                <SelectItem key={range.value} value={range.value}>{range.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" size="icon"><CalendarIcon className="h-4 w-4" /></Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="end">
              <Calendar
                mode="range"
                selected={{ from: dateRange.from, to: dateRange.to }}
                onSelect={(range) => range?.from && range?.to && setCustomRange({ from: range.from, to: range.to })}
                numberOfMonths={2}
              />
            </PopoverContent>
          </Popover>
        </div>
      </div>

      <div className="text-sm text-muted-foreground">
        Showing data from {format(dateRange.from, 'MMM d, yyyy')} to {format(dateRange.to, 'MMM d, yyyy')}
      </div>

      {isLoading ? (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-[120px] rounded-xl" />)}
          </div>
          <Skeleton className="h-[400px] rounded-xl" />
        </div>
      ) : metrics ? (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="appointments">Appointments</TabsTrigger>
            <TabsTrigger value="revenue">Revenue</TabsTrigger>
            <TabsTrigger value="utilization">Utilization</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <MetricCard title="Total Appointments" value={metrics.appointments.total} subtitle={`${metrics.appointments.completionRate}% completion rate`} icon={Users} />
              <MetricCard title="Revenue" value={formatCurrency(metrics.revenue.totalRevenue)} subtitle={`${formatCurrency(metrics.revenue.averagePerVisit)} avg/visit`} icon={DollarSign} />
              <MetricCard title="Treatment Acceptance" value={`${metrics.treatmentAcceptance.acceptanceRate}%`} subtitle={`${metrics.treatmentAcceptance.acceptedPlans} of ${metrics.treatmentAcceptance.proposedPlans} plans`} icon={TrendingUp} />
              <MetricCard title="Chair Utilization" value={`${metrics.chairUtilization.averageUtilization}%`} subtitle={`${metrics.chairUtilization.totalChairs} chairs`} icon={Clock} />
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              {[
                { label: 'No-Show Rate', value: `${metrics.appointments.noShowRate}%`, icon: AlertTriangle, bg: 'bg-red-100', text: 'text-red-600' },
                { label: 'Collected', value: formatCurrency(metrics.revenue.totalCollected), icon: CheckCircle2, bg: 'bg-green-100', text: 'text-green-600' },
                { label: 'Outstanding', value: formatCurrency(metrics.revenue.totalOutstanding), icon: XCircle, bg: 'bg-amber-100', text: 'text-amber-600' }
              ].map((m, i) => (
                <Card key={i}>
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-3">
                      <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg", m.bg)}>
                        <m.icon className={cn("h-5 w-5", m.text)} />
                      </div>
                      <div>
                        <p className="text-2xl font-bold">{m.value}</p>
                        <p className="text-sm text-muted-foreground">{m.label}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <RevenueChart data={metrics.revenue.byMonth} formatCurrency={formatCurrency} />
              <AppointmentPieChart data={metrics.appointments.byType} colors={COLORS} />
            </div>
          </TabsContent>

          <TabsContent value="appointments" className="space-y-6">
            <div className="flex justify-end">
              <Button variant="outline" onClick={() => handleExport('appointments')}><Download className="h-4 w-4 mr-2" />Export</Button>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <MetricCard title="Total" value={metrics.appointments.total} icon={Users} />
              <MetricCard title="Completed" value={metrics.appointments.completed} icon={CheckCircle2} />
              <MetricCard title="Cancelled" value={metrics.appointments.cancelled} icon={XCircle} />
              <MetricCard title="No-Shows" value={metrics.appointments.noShow} icon={AlertTriangle} />
            </div>
            <div className="grid gap-6 lg:grid-cols-2">
              <DailyAppointmentsChart data={metrics.appointments.byDay} />
              <Card>
                <CardHeader><CardTitle>Appointment Types</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  {metrics.appointments.byType.map((type, index) => (
                    <div key={type.type} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                        <span className="text-sm">{type.type}</span>
                      </div>
                      <span className="font-medium">{type.count}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="revenue" className="space-y-6">
            <div className="flex justify-end">
              <Button variant="outline" onClick={() => handleExport('revenue')}><Download className="h-4 w-4 mr-2" />Export</Button>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <MetricCard title="Total Revenue" value={formatCurrency(metrics.revenue.totalRevenue)} icon={DollarSign} />
              <MetricCard title="Collected" value={formatCurrency(metrics.revenue.totalCollected)} icon={CheckCircle2} />
              <MetricCard title="Outstanding" value={formatCurrency(metrics.revenue.totalOutstanding)} icon={Clock} />
              <MetricCard title="Avg per Visit" value={formatCurrency(metrics.revenue.averagePerVisit)} icon={TrendingUp} />
            </div>
            <div className="grid gap-6 lg:grid-cols-2">
              <MonthlyRevenueChart data={metrics.revenue.byMonth} formatCurrency={formatCurrency} />
              <Card>
                <CardHeader><CardTitle>Revenue by Procedure</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  {metrics.revenue.byProcedure.map((proc, index) => {
                    const maxRevenue = Math.max(...metrics.revenue.byProcedure.map(p => p.revenue));
                    return (
                      <div key={proc.procedure} className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span>{proc.procedure}</span>
                          <span className="font-medium">{formatCurrency(proc.revenue)}</span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div className="h-full rounded-full transition-all" style={{ width: `${(proc.revenue / maxRevenue) * 100}%`, backgroundColor: COLORS[index % COLORS.length] }} />
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="utilization" className="space-y-6">
            <div className="flex justify-end">
              <Button variant="outline" onClick={() => handleExport('utilization')}><Download className="h-4 w-4 mr-2" />Export</Button>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <MetricCard title="Average Utilization" value={`${metrics.chairUtilization.averageUtilization}%`} icon={Clock} />
              <MetricCard title="Total Chairs" value={metrics.chairUtilization.totalChairs} icon={Users} />
              <MetricCard 
                title="Peak Hour" 
                value={metrics.chairUtilization.peakHours.reduce((max, h) => h.utilization > max.utilization ? h : max).hour} 
                subtitle={`${metrics.chairUtilization.peakHours.reduce((max, h) => h.utilization > max.utilization ? h : max).utilization}% utilization`}
                icon={TrendingUp} 
              />
            </div>
            <UtilizationCharts 
              peakHours={metrics.chairUtilization.peakHours} 
              byChair={metrics.chairUtilization.byChair} 
              byDayOfWeek={metrics.chairUtilization.byDayOfWeek} 
            />
          </TabsContent>
        </Tabs>
      ) : null}
    </div>
  );
}
