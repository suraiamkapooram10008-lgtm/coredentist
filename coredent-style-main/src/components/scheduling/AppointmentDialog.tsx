// ============================================
// Appointment Dialog Component
// Create and edit appointments
// ============================================

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { format } from 'date-fns';
import { CalendarIcon, Search, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import { cn } from '@/lib/utils';
import type { ScheduleAppointment, AppointmentFormData, PatientSearchResult, ScheduleProvider } from '@/types/scheduling';
import type { Chair, AppointmentTypeConfig } from '@/types/clinic';
import { schedulingApi } from '@/services/schedulingApi';

const appointmentSchema = z.object({
  patientId: z.string().min(1, 'Patient is required'),
  patientName: z.string().min(1, 'Patient name is required'),
  providerId: z.string().min(1, 'Provider is required'),
  chairId: z.string().min(1, 'Chair is required'),
  type: z.string().min(1, 'Appointment type is required'),
  date: z.date({ required_error: 'Date is required' }),
  startTime: z.string().min(1, 'Start time is required'),
  duration: z.number().min(15, 'Duration must be at least 15 minutes'),
  notes: z.string().optional(),
});

type FormData = z.infer<typeof appointmentSchema>;

interface AppointmentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  appointment?: ScheduleAppointment | null;
  chairs: Chair[];
  providers: ScheduleProvider[];
  appointmentTypes: AppointmentTypeConfig[];
  defaultDate?: Date;
  defaultChairId?: string;
  defaultTime?: string;
  onSave: (data: AppointmentFormData) => Promise<void>;
}

// Generate time options in 15-minute intervals
function generateTimeOptions() {
  const times: string[] = [];
  for (let hour = 7; hour < 20; hour++) {
    for (let minute = 0; minute < 60; minute += 15) {
      const timeStr = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
      times.push(timeStr);
    }
  }
  return times;
}

const TIME_OPTIONS = generateTimeOptions();

export function AppointmentDialog({
  open,
  onOpenChange,
  appointment,
  chairs,
  providers,
  appointmentTypes,
  defaultDate,
  defaultChairId,
  defaultTime,
  onSave,
}: AppointmentDialogProps) {
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<PatientSearchResult[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPatient, setSelectedPatient] = useState<PatientSearchResult | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const isEditing = !!appointment;

  const form = useForm<FormData>({
    resolver: zodResolver(appointmentSchema),
    defaultValues: {
      patientId: '',
      patientName: '',
      providerId: providers[0]?.id || '',
      chairId: defaultChairId || chairs[0]?.id || '',
      type: appointmentTypes[0]?.name.toLowerCase().replace(/ /g, '_') || 'exam',
      date: defaultDate || new Date(),
      startTime: defaultTime || '09:00',
      duration: 30,
      notes: '',
    },
  });

  // Reset form when dialog opens/closes or appointment changes
  useEffect(() => {
    if (open) {
      if (appointment) {
        form.reset({
          patientId: appointment.patientId,
          patientName: appointment.patientName,
          providerId: appointment.providerId,
          chairId: appointment.chairId,
          type: appointment.type,
          date: appointment.startTime,
          startTime: format(appointment.startTime, 'HH:mm'),
          duration: appointment.duration,
          notes: appointment.notes || '',
        });
        setSelectedPatient({
          id: appointment.patientId,
          name: appointment.patientName,
          phone: appointment.patientPhone || '',
          email: '',
        });
      } else {
        form.reset({
          patientId: '',
          patientName: '',
          providerId: providers[0]?.id || '',
          chairId: defaultChairId || chairs[0]?.id || '',
          type: appointmentTypes[0]?.name.toLowerCase().replace(/ /g, '_') || 'exam',
          date: defaultDate || new Date(),
          startTime: defaultTime || '09:00',
          duration: 30,
          notes: '',
        });
        setSelectedPatient(null);
        setSearchQuery('');
      }
    }
  }, [open, appointment, form, providers, chairs, appointmentTypes, defaultDate, defaultChairId, defaultTime]);

  // Search patients
  useEffect(() => {
    const searchPatients = async () => {
      if (searchQuery.length >= 2) {
        setIsSearching(true);
        try {
          const results = await schedulingApi.searchPatients(searchQuery);
          setSearchResults(results);
        } catch (error) {
          console.error('Patient search failed:', error);
        } finally {
          setIsSearching(false);
        }
      } else {
        setSearchResults([]);
      }
    };

    const debounce = setTimeout(searchPatients, 300);
    return () => clearTimeout(debounce);
  }, [searchQuery]);

  const handlePatientSelect = (patient: PatientSearchResult) => {
    setSelectedPatient(patient);
    form.setValue('patientId', patient.id);
    form.setValue('patientName', patient.name);
    setSearchQuery('');
    setSearchResults([]);
  };

  const handleClearPatient = () => {
    setSelectedPatient(null);
    form.setValue('patientId', '');
    form.setValue('patientName', '');
  };

  const handleTypeChange = (typeName: string) => {
    const typeConfig = appointmentTypes.find(t => t.name === typeName);
    if (typeConfig) {
      form.setValue('type', typeName.toLowerCase().replace(/ /g, '_'));
      form.setValue('duration', typeConfig.duration);
    }
  };

  const onSubmit = async (data: FormData) => {
    setIsSaving(true);
    try {
      await onSave({
        patientId: data.patientId,
        patientName: data.patientName,
        providerId: data.providerId,
        chairId: data.chairId,
        type: data.type as AppointmentFormData['type'],
        date: data.date,
        startTime: data.startTime,
        duration: data.duration,
        notes: data.notes,
      });
      onOpenChange(false);
    } catch (error) {
      console.error('Failed to save appointment:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Edit Appointment' : 'New Appointment'}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          {/* Patient Search */}
          <div className="space-y-2">
            <Label>Patient</Label>
            {selectedPatient ? (
              <div className="flex items-center gap-2 p-2 border rounded-md bg-muted/50">
                <div className="flex-1">
                  <div className="font-medium">{selectedPatient.name}</div>
                  <div className="text-sm text-muted-foreground">{selectedPatient.phone}</div>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={handleClearPatient}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by name, phone, or email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
                {searchResults.length > 0 && (
                  <div className="absolute z-50 w-full mt-1 bg-popover border rounded-md shadow-md">
                    <Command>
                      <CommandList>
                        <CommandGroup>
                          {searchResults.map((patient) => (
                            <CommandItem
                              key={patient.id}
                              onSelect={() => handlePatientSelect(patient)}
                              className="cursor-pointer"
                            >
                              <div>
                                <div className="font-medium">{patient.name}</div>
                                <div className="text-sm text-muted-foreground">
                                  {patient.phone} • {patient.email}
                                </div>
                              </div>
                            </CommandItem>
                          ))}
                        </CommandGroup>
                      </CommandList>
                    </Command>
                  </div>
                )}
                {isSearching && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  </div>
                )}
              </div>
            )}
            {form.formState.errors.patientId && (
              <p className="text-sm text-destructive">
                {form.formState.errors.patientId.message}
              </p>
            )}
          </div>

          {/* Appointment Type */}
          <div className="space-y-2">
            <Label>Appointment Type</Label>
            <Select
              value={appointmentTypes.find(t => 
                t.name.toLowerCase().replace(/ /g, '_') === form.watch('type')
              )?.name || ''}
              onValueChange={handleTypeChange}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                {appointmentTypes.map((type) => (
                  <SelectItem key={type.id} value={type.name}>
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: type.color }}
                      />
                      {type.name} ({type.duration} min)
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Provider and Chair - Side by side */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Provider</Label>
              <Select
                value={form.watch('providerId')}
                onValueChange={(value) => form.setValue('providerId', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select provider" />
                </SelectTrigger>
                <SelectContent>
                  {providers.map((provider) => (
                    <SelectItem key={provider.id} value={provider.id}>
                      {provider.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Chair / Operatory</Label>
              <Select
                value={form.watch('chairId')}
                onValueChange={(value) => form.setValue('chairId', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select chair" />
                </SelectTrigger>
                <SelectContent>
                  {chairs.map((chair) => (
                    <SelectItem key={chair.id} value={chair.id}>
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: chair.color }}
                        />
                        {chair.name}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Date, Time, Duration */}
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Date</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !form.watch('date') && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {form.watch('date') ? format(form.watch('date'), 'MMM d') : 'Pick date'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={form.watch('date')}
                    onSelect={(date) => date && form.setValue('date', date)}
                    initialFocus
                    className={cn("p-3 pointer-events-auto")}
                  />
                </PopoverContent>
              </Popover>
            </div>

            <div className="space-y-2">
              <Label>Time</Label>
              <Select
                value={form.watch('startTime')}
                onValueChange={(value) => form.setValue('startTime', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select time" />
                </SelectTrigger>
                <SelectContent>
                  {TIME_OPTIONS.map((time) => {
                    const [hour, minute] = time.split(':').map(Number);
                    const displayTime = hour > 12 
                      ? `${hour - 12}:${minute.toString().padStart(2, '0')} PM`
                      : hour === 12
                        ? `12:${minute.toString().padStart(2, '0')} PM`
                        : `${hour}:${minute.toString().padStart(2, '0')} AM`;
                    return (
                      <SelectItem key={time} value={time}>
                        {displayTime}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Duration</Label>
              <Select
                value={form.watch('duration').toString()}
                onValueChange={(value) => form.setValue('duration', parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Duration" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="15">15 min</SelectItem>
                  <SelectItem value="30">30 min</SelectItem>
                  <SelectItem value="45">45 min</SelectItem>
                  <SelectItem value="60">1 hour</SelectItem>
                  <SelectItem value="90">1.5 hours</SelectItem>
                  <SelectItem value="120">2 hours</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Notes */}
          <div className="space-y-2">
            <Label>Notes (optional)</Label>
            <Textarea
              placeholder="Add any notes for this appointment..."
              {...form.register('notes')}
              rows={2}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSaving}>
              {isSaving ? 'Saving...' : isEditing ? 'Update' : 'Create Appointment'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
