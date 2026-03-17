// ============================================
// Day View Component
// Shows appointments for a single day with chair columns
// ============================================

import { useMemo, useCallback, memo } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AppointmentCard } from './AppointmentCard';
import { cn } from '@/lib/utils';
import type { ScheduleAppointment } from '@/types/scheduling';
import type { Chair } from '@/types/clinic';
import { generateTimeSlots, calculateAppointmentPosition } from '@/types/scheduling';

interface DayViewProps {
  date: Date;
  chairs: Chair[];
  appointments: ScheduleAppointment[];
  onAppointmentClick: (appointment: ScheduleAppointment) => void;
  onStatusChange: (id: string, status: string) => void;
  onEditAppointment: (appointment: ScheduleAppointment) => void;
  onCancelAppointment: (id: string) => void;
  onDropAppointment: (appointmentId: string, chairId: string, time: string) => void;
  canEdit?: boolean;
  startHour?: number;
  endHour?: number;
}

export const DayView = memo(function DayView({
  date,
  chairs,
  appointments,
  onAppointmentClick,
  onStatusChange,
  onEditAppointment,
  onCancelAppointment,
  onDropAppointment,
  canEdit = true,
  startHour = 7,
  endHour = 19,
}: DayViewProps) {
  const timeSlots = useMemo(() => generateTimeSlots(startHour, endHour), [startHour, endHour]);
  
  const getChairAppointments = useCallback((chairId: string) => {
    return appointments.filter(apt => apt.chairId === chairId);
  }, [appointments]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, chairId: string, time: string) => {
    e.preventDefault();
    const appointmentId = e.dataTransfer.getData('appointmentId');
    if (appointmentId) {
      onDropAppointment(appointmentId, chairId, time);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with chair names */}
      <div className="flex border-b sticky top-0 bg-background z-10">
        <div className="w-20 flex-shrink-0 p-2 text-xs text-muted-foreground font-medium border-r">
          Time
        </div>
        {chairs.map((chair) => (
          <div 
            key={chair.id}
            className="flex-1 min-w-[200px] p-2 text-center border-r last:border-r-0"
          >
            <div className="flex items-center justify-center gap-2">
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: chair.color }}
              />
              <span className="font-medium text-sm">{chair.name}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Time grid */}
      <ScrollArea className="flex-1">
        <div className="flex">
          {/* Time labels column */}
          <div className="w-20 flex-shrink-0 border-r">
            {timeSlots.map((slot, index) => (
              <div
                key={slot.time}
                className={cn(
                  "h-[60px] px-2 text-right text-xs text-muted-foreground border-b flex items-start pt-1",
                  slot.isHalfHour && "border-b-dashed"
                )}
              >
                {!slot.isHalfHour && (
                  <span className={cn(index === 0 ? "" : "relative -top-2")}>
                    {slot.hour > 12 
                      ? `${slot.hour - 12}:00 PM` 
                      : slot.hour === 12 
                        ? '12:00 PM'
                        : `${slot.hour}:00 AM`
                    }
                  </span>
                )}
              </div>
            ))}
          </div>

          {/* Chair columns */}
          {chairs.map((chair) => (
            <div 
              key={chair.id}
              className="flex-1 min-w-[200px] border-r last:border-r-0 relative"
            >
              {/* Time slot grid */}
              {timeSlots.map((slot) => (
                <div
                  key={slot.time}
                  className={cn(
                    "h-[60px] border-b hover:bg-muted/50 transition-colors",
                    slot.isHalfHour && "border-b-dashed"
                  )}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(e, chair.id, slot.time)}
                />
              ))}

              {/* Appointments overlay */}
              <div className="absolute inset-0 pointer-events-none">
                {getChairAppointments(chair.id).map((appointment) => {
                  const { top, height } = calculateAppointmentPosition(
                    appointment.startTime,
                    appointment.endTime,
                    startHour
                  );
                  
                  return (
                    <div key={appointment.id} className="pointer-events-auto">
                      <AppointmentCard
                        appointment={appointment}
                        style={{ top, height, position: 'absolute', left: 4, right: 4 }}
                        onClick={() => onAppointmentClick(appointment)}
                        onStatusChange={(status) => onStatusChange(appointment.id, status)}
                        onEdit={() => onEditAppointment(appointment)}
                        onCancel={() => onCancelAppointment(appointment.id)}
                        canEdit={canEdit}
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
});
