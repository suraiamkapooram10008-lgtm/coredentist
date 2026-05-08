/**
 * Dashboard Page (Refactored)
 * Main dashboard with metrics, appointments, and activity
 */

import React, { useMemo } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Users,
  Calendar,
  DollarSign,
  Clock,
  UserPlus,
  CalendarPlus,
  FileText,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { startOfMonth } from 'date-fns';
import type { UserRole } from '@/types/api';

// Custom hooks
import { useDashboardMetrics } from '@/hooks/useDashboardMetrics';
import { useTodayAppointments } from '@/hooks/useTodayAppointments';
import { useBillingSummary } from '@/hooks/useBillingSummary';
import { useFormatters } from '@/hooks/useFormatters';
import { useRecentActivity } from '@/hooks/useRecentActivity';

// Components
import { DashboardStatCard } from '@/components/dashboard/DashboardStatCard';
import { DashboardScheduleCard } from '@/components/dashboard/DashboardScheduleCard';
import { DashboardActivityCard } from '@/components/dashboard/DashboardActivityCard';

const quickActions = [
  {
    label: 'New Patient',
    icon: UserPlus,
    href: '/patients',
    roles: ['owner', 'admin', 'front_desk'],
  },
  {
    label: 'Book Appointment',
    icon: CalendarPlus,
    href: '/schedule',
    roles: ['owner', 'admin', 'front_desk', 'dentist'],
  },
  {
    label: 'Clinical Notes',
    icon: FileText,
    href: '/notes',
    roles: ['owner', 'admin', 'dentist'],
  },
];

/**
 * Get greeting based on time of day
 */
function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

/**
 * Dashboard Page Component
 */
export default function Dashboard() {
  const { user, hasRole } = useAuth();
  const navigate = useNavigate();
  const { formatCurrency } = useFormatters();

  // Calculate date ranges
  const today = useMemo(() => new Date(), []);
  const startOfToday = useMemo(() => {
    const date = new Date(today);
    date.setHours(0, 0, 0, 0);
    return date;
  }, [today]);
  const endOfToday = useMemo(() => {
    const date = new Date(today);
    date.setHours(23, 59, 59, 999);
    return date;
  }, [today]);
  const monthStart = useMemo(() => startOfMonth(today), [today]);

  // Fetch data using custom hooks
  const { metrics, isLoading: isLoadingMetrics } = useDashboardMetrics({
    from: monthStart,
    to: today,
  });

  const { appointments, upcomingAppointments, upcomingCount, uniquePatientsCount, isLoading: isLoadingAppointments } = useTodayAppointments({
    startDate: startOfToday,
    endDate: endOfToday,
  });

  const { billingSummary, pendingCount, isLoading: isLoadingBilling } = useBillingSummary();

  // Process recent activity
  const { activities } = useRecentActivity(appointments, { limit: 4 });

  const isLoading = isLoadingMetrics || isLoadingAppointments || isLoadingBilling;

  // Filter quick actions by role
  const filteredQuickActions = quickActions.filter(action =>
    action.roles.some(role => hasRole(role as UserRole))
  );

  // Build stat cards
  const statCards = [
    {
      title: "Today's Appointments",
      value: appointments.length,
      icon: Calendar,
      description: `${upcomingCount} upcoming today`,
      trend: 'Updated today',
      href: '/schedule',
    },
    {
      title: 'Patients Today',
      value: uniquePatientsCount,
      icon: Users,
      description: 'Unique patients',
      trend: 'Updated today',
      href: '/patients',
    },
    {
      title: 'Pending Checkouts',
      value: pendingCount,
      icon: Clock,
      description: 'Invoices awaiting payment',
      trend: 'Updated today',
      href: '/billing',
    },
    {
      title: 'Monthly Revenue',
      value: formatCurrency(metrics?.revenue.totalRevenue ?? 0),
      icon: DollarSign,
      description: new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
      trend: 'Updated today',
      href: '/reports',
    },
  ];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col gap-2">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-[400px] w-full" />
          <Skeleton className="h-[400px] w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
      {/* Welcome Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {getGreeting()}, {user?.firstName}! 👋
          </h1>
          <p className="text-muted-foreground mt-1 text-lg">
            Here's what's happening at {user?.practiceName} today.
          </p>
        </div>

        {/* Quick Actions */}
        <div className="flex gap-2 flex-wrap">
          {filteredQuickActions.map((action) => (
            <Button
              key={action.href}
              variant="outline"
              size="sm"
              className="gap-2 h-10 px-4 shadow-sm hover:bg-secondary"
              onClick={() => navigate(action.href)}
            >
              <action.icon className="h-4 w-4" />
              <span>{action.label}</span>
            </Button>
          ))}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 stagger-fade-in">
        {statCards.map((stat) => (
          <DashboardStatCard
            key={stat.title}
            title={stat.title}
            value={stat.value}
            icon={stat.icon}
            description={stat.description}
            trend={stat.trend}
            href={stat.href}
          />
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        <DashboardScheduleCard appointments={upcomingAppointments} />
        <DashboardActivityCard activities={activities} />
      </div>
    </div>
  );
}
