// ============================================
// Appointment Card Component
// Displays a single appointment in the schedule grid
// ============================================

import { useState, memo } from 'react';
import { 
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuTrigger,
} from '@/components/ui/context-menu';
import { 
  Clock, 
  User, 
  Phone,
  CheckCircle2,
  XCircle,
  UserCheck,
  Play,
  Ban,
  Edit
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ScheduleAppointment } from '@/types/scheduling';
import { appointmentStatusConfig, formatTime } from '@/types/scheduling';
import { defaultAppointmentTypes } from '@/types/clinic';

interface AppointmentCardProps {
  appointment: ScheduleAppointment;
  style?: React.CSSProperties;
  onClick?: () => void;
  onStatusChange?: (status: string) => void;
  onEdit?: () => void;
  onCancel?: () => void;
  isDragging?: boolean;
  canEdit?: boolean;
}

export const AppointmentCard = memo(function AppointmentCard({
  appointment,
  style,
  onClick,
  onStatusChange,
  onEdit,
  onCancel,
  isDragging,
  canEdit = true,
}: AppointmentCardProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  
  const typeConfig = defaultAppointmentTypes.find(t => 
    t.name.toLowerCase().includes(appointment.type.replace('_', ' '))
  );
  const statusConfig = appointmentStatusConfig[appointment.status];
  
  const bgColor = typeConfig?.color || '#6B7280';
  
  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.setData('appointmentId', appointment.id);
    e.dataTransfer.setData('originalChairId', appointment.chairId);
    e.dataTransfer.setData('originalStartTime', appointment.startTime.toISOString());
    e.dataTransfer.effectAllowed = 'move';
  };

  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>
        <div
          className={cn(
            "absolute left-1 right-1 rounded-md p-2 cursor-pointer transition-all",
            "border-l-4 shadow-sm hover:shadow-md",
            isDragging && "opacity-50 scale-95",
            isDragOver && "ring-2 ring-primary"
          )}
          style={{
            ...style,
            backgroundColor: `${bgColor}15`,
            borderLeftColor: bgColor,
          }}
          onClick={onClick}
          draggable={canEdit}
          onDragStart={handleDragStart}
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={() => setIsDragOver(false)}
        >
          {/* Patient name */}
          <div className="font-medium text-sm truncate flex items-center gap-1">
            <User className="h-3 w-3 flex-shrink-0" />
            {appointment.patientName}
          </div>
          
          {/* Time */}
          <div className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
            <Clock className="h-3 w-3" />
            {formatTime(appointment.startTime)} - {formatTime(appointment.endTime)}
          </div>
          
          {/* Type and Status badges */}
          <div className="flex items-center gap-1 mt-1 flex-wrap">
            <span 
              className="text-xs px-1.5 py-0.5 rounded-full text-white"
              style={{ backgroundColor: bgColor }}
            >
              {typeConfig?.name || appointment.type}
            </span>
            <span className={cn("text-xs px-1.5 py-0.5 rounded-full", statusConfig.bgClass)}>
              {statusConfig.label}
            </span>
          </div>

          {/* Provider */}
          {style && (style.height as number) > 80 && (
            <div className="text-xs text-muted-foreground mt-1 truncate">
              {appointment.providerName}
            </div>
          )}

          {/* Phone (if space allows) */}
          {style && (style.height as number) > 100 && appointment.patientPhone && (
            <div className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
              <Phone className="h-3 w-3" />
              {appointment.patientPhone}
            </div>
          )}
        </div>
      </ContextMenuTrigger>
      
      <ContextMenuContent className="w-48">
        {canEdit && (
          <>
            <ContextMenuItem onClick={onEdit} className="gap-2">
              <Edit className="h-4 w-4" />
              Edit Appointment
            </ContextMenuItem>
            <ContextMenuSeparator />
          </>
        )}
        
        <ContextMenuItem 
          onClick={() => onStatusChange?.('confirmed')}
          disabled={appointment.status === 'confirmed'}
          className="gap-2"
        >
          <CheckCircle2 className="h-4 w-4 text-blue-600" />
          Mark Confirmed
        </ContextMenuItem>
        
        <ContextMenuItem 
          onClick={() => onStatusChange?.('checked_in')}
          disabled={appointment.status === 'checked_in'}
          className="gap-2"
        >
          <UserCheck className="h-4 w-4 text-green-600" />
          Check In
        </ContextMenuItem>
        
        <ContextMenuItem 
          onClick={() => onStatusChange?.('in_progress')}
          disabled={appointment.status === 'in_progress'}
          className="gap-2"
        >
          <Play className="h-4 w-4 text-amber-600" />
          Start Treatment
        </ContextMenuItem>
        
        <ContextMenuItem 
          onClick={() => onStatusChange?.('completed')}
          disabled={appointment.status === 'completed'}
          className="gap-2"
        >
          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          Mark Complete
        </ContextMenuItem>
        
        <ContextMenuSeparator />
        
        <ContextMenuItem 
          onClick={() => onStatusChange?.('no_show')}
          disabled={appointment.status === 'no_show'}
          className="gap-2 text-orange-600"
        >
          <Ban className="h-4 w-4" />
          No Show
        </ContextMenuItem>
        
        {canEdit && (
          <ContextMenuItem 
            onClick={onCancel}
            disabled={appointment.status === 'cancelled'}
            className="gap-2 text-destructive"
          >
            <XCircle className="h-4 w-4" />
            Cancel Appointment
          </ContextMenuItem>
        )}
      </ContextMenuContent>
    </ContextMenu>
  );
});
