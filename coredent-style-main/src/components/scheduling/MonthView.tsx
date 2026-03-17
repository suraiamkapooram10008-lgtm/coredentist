// ============================================
// Month View Component
// Calendar grid showing appointments for a month
// ============================================

import { useMemo } from 'react';
import { 
  format, 
  startOfMonth, 
  endOfMonth, 
  startOfWeek, 
  endOfWeek, 
  eachDayOfInterval,
  isSameMonth,
  isSameDay,
  isToday 
} from 'date-fns';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { ScheduleAppointment } from '@/types/scheduling';
import { appointmentStatusConfig } from '@/types/scheduling';
import { defaultAppointmentTypes } from '@/types/clinic';

interface MonthViewProps {
  currentDate: Date;
  appointments: ScheduleAppointment[];
  onDayClick: (date: Date) => void;
  onAppointmentClick: (appointment: ScheduleAppointment) => void;
}

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export function MonthView({
  currentDate,
  appointments,
  onDayClick,
  onAppointmentClick,
}: MonthViewProps) {
  // Generate all days to display in the calendar grid
  const calendarDays = useMemo(() => {
    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(currentDate);
    const calendarStart = startOfWeek(monthStart, { weekStartsOn: 0 });
    const calendarEnd = endOfWeek(monthEnd, { weekStartsOn: 0 });
    
    return eachDayOfInterval({ start: calendarStart, end: calendarEnd });
  }, [currentDate]);

  const getAppointmentsForDay = (date: Date) => {
    return appointments.filter(apt => isSameDay(apt.startTime, date));
  };

  return (
    <div className="flex flex-col h-full">
      {/* Weekday headers */}
      <div className="grid grid-cols-7 border-b">
        {WEEKDAYS.map((day) => (
          <div 
            key={day}
            className="p-2 text-center text-sm font-medium text-muted-foreground border-r last:border-r-0"
          >
            {day}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="flex-1 grid grid-cols-7 grid-rows-[repeat(auto-fill,minmax(120px,1fr))]">
        {calendarDays.map((day) => {
          const dayAppointments = getAppointmentsForDay(day);
          const isCurrentMonth = isSameMonth(day, currentDate);
          const isCurrentDay = isToday(day);

          return (
            <div
              key={day.toISOString()}
              className={cn(
                "min-h-[120px] border-r border-b p-1 cursor-pointer hover:bg-muted/50 transition-colors",
                !isCurrentMonth && "bg-muted/30 text-muted-foreground",
                isCurrentDay && "bg-primary/5"
              )}
              onClick={() => onDayClick(day)}
            >
              {/* Day number */}
              <div className={cn(
                "text-sm font-medium mb-1",
                isCurrentDay && "text-primary"
              )}>
                <span className={cn(
                  "inline-flex items-center justify-center w-6 h-6 rounded-full",
                  isCurrentDay && "bg-primary text-primary-foreground"
                )}>
                  {format(day, 'd')}
                </span>
              </div>

              {/* Appointments preview */}
              <ScrollArea className="h-[calc(100%-24px)]">
                <div className="space-y-1">
                  {dayAppointments.slice(0, 3).map((appointment) => {
                    const typeConfig = defaultAppointmentTypes.find(t => 
                      t.name.toLowerCase().includes(appointment.type.replace('_', ' '))
                    );
                    
                    return (
                      <div
                        key={appointment.id}
                        className="text-xs p-1 rounded truncate cursor-pointer hover:opacity-80"
                        style={{ 
                          backgroundColor: `${typeConfig?.color || '#6B7280'}20`,
                          borderLeft: `2px solid ${typeConfig?.color || '#6B7280'}`
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onAppointmentClick(appointment);
                        }}
                      >
                        <span className="font-medium">
                          {format(appointment.startTime, 'h:mm a')}
                        </span>
                        {' '}
                        <span className="text-muted-foreground">
                          {appointment.patientName}
                        </span>
                      </div>
                    );
                  })}
                  
                  {dayAppointments.length > 3 && (
                    <div className="text-xs text-muted-foreground text-center">
                      +{dayAppointments.length - 3} more
                    </div>
                  )}
                </div>
              </ScrollArea>
            </div>
          );
        })}
      </div>
    </div>
  );
}
