// ============================================
// Week View Component
// Shows appointments for a week with day columns
// ============================================

import { useMemo } from 'react';
import { format, addDays, startOfWeek, isSameDay, isToday } from 'date-fns';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AppointmentCard } from './AppointmentCard';
import { cn } from '@/lib/utils';
import type { ScheduleAppointment } from '@/types/scheduling';
import { generateTimeSlots, calculateAppointmentPosition } from '@/types/scheduling';

interface WeekViewProps {
  currentDate: Date;
  appointments: ScheduleAppointment[];
  onAppointmentClick: (appointment: ScheduleAppointment) => void;
  onStatusChange: (id: string, status: string) => void;
  onEditAppointment: (appointment: ScheduleAppointment) => void;
  onCancelAppointment: (id: string) => void;
  onDropAppointment: (appointmentId: string, date: Date, time: string) => void;
  onDayClick: (date: Date) => void;
  canEdit?: boolean;
  startHour?: number;
  endHour?: number;
}

export function WeekView({
  currentDate,
  appointments,
  onAppointmentClick,
  onStatusChange,
  onEditAppointment,
  onCancelAppointment,
  onDropAppointment,
  onDayClick,
  canEdit = true,
  startHour = 7,
  endHour = 19,
}: WeekViewProps) {
  const timeSlots = useMemo(() => generateTimeSlots(startHour, endHour), [startHour, endHour]);
  
  const weekDays = useMemo(() => {
    const start = startOfWeek(currentDate, { weekStartsOn: 0 });
    return Array.from({ length: 7 }, (_, i) => addDays(start, i));
  }, [currentDate]);

  const getAppointmentsForDay = (date: Date) => {
    return appointments.filter(apt => isSameDay(apt.startTime, date));
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, date: Date, time: string) => {
    e.preventDefault();
    const appointmentId = e.dataTransfer.getData('appointmentId');
    if (appointmentId) {
      onDropAppointment(appointmentId, date, time);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with day names */}
      <div className="flex border-b sticky top-0 bg-background z-10">
        <div className="w-16 flex-shrink-0 p-2 text-xs text-muted-foreground font-medium border-r">
          Time
        </div>
        {weekDays.map((day) => (
          <div 
            key={day.toISOString()}
            className={cn(
              "flex-1 min-w-[120px] p-2 text-center border-r last:border-r-0 cursor-pointer hover:bg-muted/50",
              isToday(day) && "bg-primary/5"
            )}
            onClick={() => onDayClick(day)}
          >
            <div className="text-xs text-muted-foreground">{format(day, 'EEE')}</div>
            <div className={cn(
              "text-lg font-semibold",
              isToday(day) && "text-primary"
            )}>
              {format(day, 'd')}
            </div>
          </div>
        ))}
      </div>

      {/* Time grid */}
      <ScrollArea className="flex-1">
        <div className="flex">
          {/* Time labels column */}
          <div className="w-16 flex-shrink-0 border-r">
            {timeSlots.map((slot, index) => (
              <div
                key={slot.time}
                className={cn(
                  "h-[40px] px-1 text-right text-xs text-muted-foreground border-b flex items-start pt-1",
                  slot.isHalfHour && "border-b-dashed"
                )}
              >
                {!slot.isHalfHour && (
                  <span className={cn("text-[10px]", index === 0 ? "" : "relative -top-2")}>
                    {slot.hour > 12 
                      ? `${slot.hour - 12} PM` 
                      : slot.hour === 12 
                        ? '12 PM'
                        : `${slot.hour} AM`
                    }
                  </span>
                )}
              </div>
            ))}
          </div>

          {/* Day columns */}
          {weekDays.map((day) => (
            <div 
              key={day.toISOString()}
              className={cn(
                "flex-1 min-w-[120px] border-r last:border-r-0 relative",
                isToday(day) && "bg-primary/5"
              )}
            >
              {/* Time slot grid */}
              {timeSlots.map((slot) => (
                <div
                  key={slot.time}
                  className={cn(
                    "h-[40px] border-b hover:bg-muted/50 transition-colors",
                    slot.isHalfHour && "border-b-dashed"
                  )}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(e, day, slot.time)}
                />
              ))}

              {/* Appointments overlay */}
              <div className="absolute inset-0 pointer-events-none">
                {getAppointmentsForDay(day).map((appointment) => {
                  const { top, height } = calculateAppointmentPosition(
                    appointment.startTime,
                    appointment.endTime,
                    startHour
                  );
                  // Scale for week view (40px per slot instead of 60px)
                  const scaledTop = top * (40 / 60);
                  const scaledHeight = Math.max(height * (40 / 60), 24);
                  
                  return (
                    <div key={appointment.id} className="pointer-events-auto">
                      <AppointmentCard
                        appointment={appointment}
                        style={{ 
                          top: scaledTop, 
                          height: scaledHeight, 
                          position: 'absolute', 
                          left: 2, 
                          right: 2 
                        }}
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
}
