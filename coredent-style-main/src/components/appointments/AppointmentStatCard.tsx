/**
 * AppointmentStatCard Component
 * Displays a single appointment statistic
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { LucideIcon } from 'lucide-react';

interface AppointmentStatCardProps {
  title: string;
  value: number;
  icon: LucideIcon;
  color: string;
  isLoading?: boolean;
}

/**
 * Memoized stat card for appointment statistics
 */
export const AppointmentStatCard = React.memo(function AppointmentStatCard({
  title,
  value,
  icon: Icon,
  color,
  isLoading = false,
}: AppointmentStatCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={`h-4 w-4 ${color}`} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-8 w-12 animate-pulse rounded bg-muted" />
        ) : (
          <>
            <div className={`text-2xl font-bold ${color}`}>{value}</div>
            <p className="text-xs text-muted-foreground">
              {title.toLowerCase()}
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
});
