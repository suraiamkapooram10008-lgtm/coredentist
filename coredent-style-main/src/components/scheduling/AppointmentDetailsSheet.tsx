// ============================================
// Appointment Details Sheet
// View full appointment details in a side panel
// ============================================

import { format } from 'date-fns';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  User,
  Phone,
  Clock,
  Calendar,
  MapPin,
  Stethoscope,
  FileText,
  Edit,
  XCircle,
  CheckCircle2,
  UserCheck,
  Play,
} from 'lucide-react';
import type { ScheduleAppointment } from '@/types/scheduling';
import type { AppointmentStatus } from '@/types/api';
import { appointmentStatusConfig, formatTime } from '@/types/scheduling';
import { defaultAppointmentTypes } from '@/types/clinic';

interface AppointmentDetailsSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  appointment: ScheduleAppointment | null;
  onEdit: () => void;
  onStatusChange: (status: AppointmentStatus) => void;
  onCancel: () => void;
  canEdit?: boolean;
}

export function AppointmentDetailsSheet({
  open,
  onOpenChange,
  appointment,
  onEdit,
  onStatusChange,
  onCancel,
  canEdit = true,
}: AppointmentDetailsSheetProps) {
  if (!appointment) return null;

  const typeConfig = defaultAppointmentTypes.find(t => 
    t.name.toLowerCase().includes(appointment.type.replace('_', ' '))
  );
  const statusConfig = appointmentStatusConfig[appointment.status];

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[400px]">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <div 
              className="w-4 h-4 rounded-full"
              style={{ backgroundColor: typeConfig?.color || '#6B7280' }}
            />
            {typeConfig?.name || appointment.type}
          </SheetTitle>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Status */}
          <div>
            <Badge className={statusConfig.bgClass}>
              {statusConfig.label}
            </Badge>
          </div>

          {/* Patient Info */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-muted-foreground">Patient</h4>
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                <User className="h-5 w-5 text-primary" />
              </div>
              <div>
                <div className="font-medium">{appointment.patientName}</div>
                {appointment.patientPhone && (
                  <div className="text-sm text-muted-foreground flex items-center gap-1">
                    <Phone className="h-3 w-3" />
                    {appointment.patientPhone}
                  </div>
                )}
              </div>
            </div>
          </div>

          <Separator />

          {/* Date & Time */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-muted-foreground">Date & Time</h4>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                {format(appointment.startTime, 'EEEE, MMMM d, yyyy')}
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Clock className="h-4 w-4 text-muted-foreground" />
                {formatTime(appointment.startTime)} - {formatTime(appointment.endTime)}
                <span className="text-muted-foreground">({appointment.duration} min)</span>
              </div>
            </div>
          </div>

          <Separator />

          {/* Provider & Location */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-muted-foreground">Provider & Location</h4>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <Stethoscope className="h-4 w-4 text-muted-foreground" />
                {appointment.providerName}
              </div>
              <div className="flex items-center gap-2 text-sm">
                <MapPin className="h-4 w-4 text-muted-foreground" />
                {appointment.chairName}
              </div>
            </div>
          </div>

          {/* Notes */}
          {appointment.notes && (
            <>
              <Separator />
              <div className="space-y-3">
                <h4 className="text-sm font-medium text-muted-foreground">Notes</h4>
                <div className="flex items-start gap-2 text-sm">
                  <FileText className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <p className="text-sm">{appointment.notes}</p>
                </div>
              </div>
            </>
          )}

          <Separator />

          {/* Quick Actions */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-muted-foreground">Quick Actions</h4>
            <div className="grid grid-cols-2 gap-2">
              {appointment.status === 'scheduled' && (
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => onStatusChange('confirmed')}
                  className="gap-2"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  Confirm
                </Button>
              )}
              {(appointment.status === 'scheduled' || appointment.status === 'confirmed') && (
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => onStatusChange('checked_in')}
                  className="gap-2"
                >
                  <UserCheck className="h-4 w-4" />
                  Check In
                </Button>
              )}
              {appointment.status === 'checked_in' && (
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => onStatusChange('in_progress')}
                  className="gap-2"
                >
                  <Play className="h-4 w-4" />
                  Start
                </Button>
              )}
              {appointment.status === 'in_progress' && (
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => onStatusChange('completed')}
                  className="gap-2"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  Complete
                </Button>
              )}
            </div>
          </div>

          {/* Main Actions */}
          <div className="flex gap-2 pt-4">
            {canEdit && (
              <>
                <Button onClick={onEdit} className="flex-1 gap-2">
                  <Edit className="h-4 w-4" />
                  Edit
                </Button>
                {appointment.status !== 'cancelled' && (
                  <Button 
                    variant="destructive" 
                    onClick={onCancel}
                    className="gap-2"
                  >
                    <XCircle className="h-4 w-4" />
                    Cancel
                  </Button>
                )}
              </>
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
