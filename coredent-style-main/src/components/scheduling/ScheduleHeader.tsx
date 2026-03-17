// ============================================
// Schedule Header Component
// Navigation controls and view switcher
// ============================================

import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  ChevronLeft, 
  ChevronRight, 
  CalendarDays, 
  Plus,
  Search
} from 'lucide-react';
import type { CalendarView } from '@/types/scheduling';
import { cn } from '@/lib/utils';

interface ScheduleHeaderProps {
  formattedDate: string;
  currentDate: Date;
  view: CalendarView;
  onViewChange: (view: CalendarView) => void;
  onPrevious: () => void;
  onNext: () => void;
  onToday: () => void;
  onDateSelect: (date: Date) => void;
  onNewAppointment: () => void;
  onOpenSearch: () => void;
}

export function ScheduleHeader({
  formattedDate,
  currentDate,
  view,
  onViewChange,
  onPrevious,
  onNext,
  onToday,
  onDateSelect,
  onNewAppointment,
  onOpenSearch,
}: ScheduleHeaderProps) {
  return (
    <div className="flex flex-col gap-4 pb-4 border-b">
      {/* Top row: Title and actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold">Schedule</h1>
          <Button onClick={onToday} variant="outline" size="sm">
            Today
          </Button>
        </div>
        
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={onOpenSearch}
            className="gap-2"
          >
            <Search className="h-4 w-4" />
            <span className="hidden sm:inline">Find Patient</span>
          </Button>
          <Button onClick={onNewAppointment} size="sm" className="gap-2">
            <Plus className="h-4 w-4" />
            <span className="hidden sm:inline">New Appointment</span>
          </Button>
        </div>
      </div>

      {/* Bottom row: Navigation and view switcher */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={onPrevious}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="ghost" className="gap-2 font-medium">
                <CalendarDays className="h-4 w-4" />
                {formattedDate}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                mode="single"
                selected={currentDate}
                onSelect={(date) => date && onDateSelect(date)}
                initialFocus
                className={cn("p-3 pointer-events-auto")}
              />
            </PopoverContent>
          </Popover>
          
          <Button variant="ghost" size="icon" onClick={onNext}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        <Tabs value={view} onValueChange={(v) => onViewChange(v as CalendarView)}>
          <TabsList>
            <TabsTrigger value="day">Day</TabsTrigger>
            <TabsTrigger value="week">Week</TabsTrigger>
            <TabsTrigger value="month">Month</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>
    </div>
  );
}
