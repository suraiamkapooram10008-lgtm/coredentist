/**
 * AppointmentListView Component
 * Displays appointments in a virtualized table
 */

import React, { useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Clock, User, Edit, Send, Trash2, Loader2 } from 'lucide-react';
import { getStatusColor } from '@/hooks/useAppointmentFilters';
import type { Appointment } from '@/services/appointmentsApi';

interface AppointmentListViewProps {
  appointments: Appointment[];
  isLoading?: boolean;
  onEdit?: (appointment: Appointment) => void;
  onSendReminder?: (id: string) => void;
  onDelete?: (id: string) => void;
}

/**
 * Virtualized appointment list view
 */
export const AppointmentListView = React.memo(function AppointmentListView({
  appointments,
  isLoading = false,
  onEdit,
  onSendReminder,
  onDelete,
}: AppointmentListViewProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  const rowVirtualizer = useVirtualizer({
    count: appointments.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 72,
    overscan: 5,
  });

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
      <CardContent className="p-0">
        <div ref={parentRef} className="overflow-auto max-h-[600px] relative">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Patient</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Dentist</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody
              style={{
                height: `${rowVirtualizer.getTotalSize()}px`,
                position: 'relative',
              }}
            >
              {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                const apt = appointments[virtualRow.index];
                return (
                  <TableRow
                    key={apt.id}
                    data-index={virtualRow.index}
                    ref={rowVirtualizer.measureElement}
                  >
                    <TableCell className="font-medium flex-1">
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        {apt.time}
                      </div>
                    </TableCell>
                    <TableCell className="flex-1">
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-muted-foreground" />
                        {apt.patient || apt.patientName}
                      </div>
                    </TableCell>
                    <TableCell className="w-[120px]">
                      <Badge variant="outline">{apt.type}</Badge>
                    </TableCell>
                    <TableCell className="flex-1">{apt.dentist}</TableCell>
                    <TableCell className="w-[100px]">{apt.duration}</TableCell>
                    <TableCell className="w-[120px]">
                      <Badge className={getStatusColor(apt.status)}>
                        {apt.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="w-[150px]">
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => onEdit?.(apt)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => onSendReminder?.(apt.id)}
                        >
                          <Send className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => onDelete?.(apt.id)}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
});
