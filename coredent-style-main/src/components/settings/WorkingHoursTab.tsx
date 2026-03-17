// ============================================
// CoreDent PMS - Working Hours Tab
// Configure clinic working days and hours
// ============================================

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2, Save, Clock, Copy } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import type { WorkingHours, DaySchedule } from '@/types/clinic';
import { clinicApi } from '@/services/clinicApi';

interface WorkingHoursTabProps {
  workingHours: WorkingHours;
  onUpdate: (workingHours: WorkingHours) => void;
}

type DayKey = keyof WorkingHours;

const DAYS: { key: DayKey; label: string }[] = [
  { key: 'monday', label: 'Monday' },
  { key: 'tuesday', label: 'Tuesday' },
  { key: 'wednesday', label: 'Wednesday' },
  { key: 'thursday', label: 'Thursday' },
  { key: 'friday', label: 'Friday' },
  { key: 'saturday', label: 'Saturday' },
  { key: 'sunday', label: 'Sunday' },
];

// Generate time options in 15-minute increments
const generateTimeOptions = () => {
  const options: string[] = [];
  for (let hour = 0; hour < 24; hour++) {
    for (let minute = 0; minute < 60; minute += 15) {
      const h = hour.toString().padStart(2, '0');
      const m = minute.toString().padStart(2, '0');
      options.push(`${h}:${m}`);
    }
  }
  return options;
};

const TIME_OPTIONS = generateTimeOptions();

const formatTime = (time: string) => {
  const [hours, minutes] = time.split(':');
  const hour = parseInt(hours);
  const ampm = hour >= 12 ? 'PM' : 'AM';
  const displayHour = hour % 12 || 12;
  return `${displayHour}:${minutes} ${ampm}`;
};

export function WorkingHoursTab({ workingHours, onUpdate }: WorkingHoursTabProps) {
  const [hours, setHours] = useState<WorkingHours>({ ...workingHours });
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();

  const handleDayChange = (day: DayKey, field: keyof DaySchedule, value: string | boolean) => {
    setHours(prev => ({
      ...prev,
      [day]: {
        ...prev[day],
        [field]: value,
      },
    }));
  };

  const copyToAllWeekdays = (sourceDay: DayKey) => {
    const sourceSchedule = hours[sourceDay];
    const weekdays: DayKey[] = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
    
    setHours(prev => {
      const updated = { ...prev };
      weekdays.forEach(day => {
        updated[day] = { ...sourceSchedule };
      });
      return updated;
    });

    toast({
      title: 'Schedule Copied',
      description: 'Applied to all weekdays (Mon-Fri)',
    });
  };

  const handleSave = async () => {
    setIsSaving(true);

    try {
      const response = await clinicApi.updateSettings({ workingHours: hours });
      if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Failed to save hours');
      }
      onUpdate(response.data.workingHours);

      toast({
        title: 'Hours Saved',
        description: 'Working hours have been updated.',
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to save hours. Please try again.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Working Hours
          </CardTitle>
          <CardDescription>
            Set your clinic's operating hours for each day of the week
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {DAYS.map(({ key, label }) => (
              <div
                key={key}
                className={`flex flex-col sm:flex-row sm:items-center gap-4 p-4 rounded-lg border ${
                  hours[key].isOpen ? 'bg-card' : 'bg-muted/50'
                }`}
              >
                {/* Day Name & Toggle */}
                <div className="flex items-center justify-between sm:w-32">
                  <Label className="font-medium">{label}</Label>
                  <Switch
                    checked={hours[key].isOpen}
                    onCheckedChange={(checked) => handleDayChange(key, 'isOpen', checked)}
                  />
                </div>

                {/* Time Selectors */}
                {hours[key].isOpen ? (
                  <div className="flex flex-1 flex-wrap items-center gap-4">
                    <div className="flex items-center gap-2">
                      <Label className="text-sm text-muted-foreground">Open</Label>
                      <Select
                        value={hours[key].openTime}
                        onValueChange={(value) => handleDayChange(key, 'openTime', value)}
                      >
                        <SelectTrigger className="w-[110px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {TIME_OPTIONS.map((time) => (
                            <SelectItem key={time} value={time}>
                              {formatTime(time)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <span className="text-muted-foreground">to</span>

                    <div className="flex items-center gap-2">
                      <Label className="text-sm text-muted-foreground">Close</Label>
                      <Select
                        value={hours[key].closeTime}
                        onValueChange={(value) => handleDayChange(key, 'closeTime', value)}
                      >
                        <SelectTrigger className="w-[110px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {TIME_OPTIONS.map((time) => (
                            <SelectItem key={time} value={time}>
                              {formatTime(time)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Copy to All Button (show only for weekdays) */}
                    {['monday', 'tuesday', 'wednesday', 'thursday', 'friday'].includes(key) && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToAllWeekdays(key)}
                        className="gap-1 text-xs"
                      >
                        <Copy className="h-3 w-3" />
                        Apply to weekdays
                      </Button>
                    )}
                  </div>
                ) : (
                  <div className="flex-1 text-sm text-muted-foreground">
                    Closed
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={isSaving} size="lg" className="gap-2">
          {isSaving ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4" />
              Save Hours
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
