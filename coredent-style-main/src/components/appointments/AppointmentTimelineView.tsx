/**
 * AppointmentTimelineView Component
 * Displays appointments in a timeline format
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2 } from 'lucide-react';
import { getStatusColor } from '@/hooks/useAppointmentFilters';
import type { Appointment } from '@/services/appointmentsApi';

interface AppointmentTimelineViewProps {
  appointments: Appointment[];
  isLoading?: boolean;
}

/**
 * Timeline view for appointments
 */
export const AppointmentTimelineView = React.memo(function AppointmentTimelineView({
  appointments,
  isLoading = false,
}: AppointmentTimelineViewProps) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (appointments.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-8 text-muted-foreground">
          No appointments found
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Timeline View</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {appointments.map((apt) => (
            <div
              key={apt.id}
              className="flex gap-4 p-3 border rounded-lg hover:bg-muted/50 transition-colors"
              data-testid={`appointment-apt-${apt.id}`}
            >
              <div className="w-20 font-medium text-sm">{apt.time}</div>
              <div className="flex-1">
                <p className="font-medium">{apt.patient || apt.patientName}</p>
                <p className="text-sm text-muted-foreground">
                  {apt.type} - {apt.dentist}
                </p>
              </div>
              <Badge className={getStatusColor(apt.status)}>
                {apt.status}
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
});
