/**
 * AppointmentForm Component
 * Form for creating/editing appointments
 */

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DialogFooter } from '@/components/ui/dialog';
import type { Appointment } from '@/services/appointmentsApi';

interface AppointmentType {
  id: string;
  name: string;
  duration: number;
}

interface AppointmentFormProps {
  appointment?: Appointment | null;
  appointmentTypes?: AppointmentType[];
  onSubmit?: (data: Partial<Appointment>) => void;
  onCancel?: () => void;
}

/**
 * Form for creating and editing appointments
 */
export const AppointmentForm = React.memo(function AppointmentForm({
  appointment,
  appointmentTypes = [],
  onSubmit,
  onCancel,
}: AppointmentFormProps) {
  const [formData, setFormData] = useState<Partial<Appointment>>(
    appointment || {
      patient: '',
      patientName: '',
      time: '',
      duration: '30',
      type: '',
      dentist: '',
      status: 'Pending',
    }
  );

  // Reset form when appointment changes
  useEffect(() => {
    if (appointment) {
      setFormData(appointment);
    }
  }, [appointment]);

  const handleChange = (field: keyof Appointment, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit?.(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="patient">Patient Name</Label>
        <Input
          id="patient"
          value={formData.patient || ''}
          onChange={(e) => handleChange('patient', e.target.value)}
          placeholder="Enter patient name"
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="time">Time</Label>
        <Input
          id="time"
          value={formData.time || ''}
          onChange={(e) => handleChange('time', e.target.value)}
          placeholder="e.g., 9:00 AM"
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="duration">Duration (minutes)</Label>
        <Input
          id="duration"
          type="number"
          value={formData.duration || '30'}
          onChange={(e) => handleChange('duration', e.target.value)}
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="type">Appointment Type</Label>
        <Select
          value={formData.type || ''}
          onValueChange={(value) => handleChange('type', value)}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select type" />
          </SelectTrigger>
          <SelectContent>
            {appointmentTypes.map((type) => (
              <SelectItem key={type.id} value={type.name}>
                {type.name} ({type.duration} min)
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="dentist">Dentist</Label>
        <Input
          id="dentist"
          value={formData.dentist || ''}
          onChange={(e) => handleChange('dentist', e.target.value)}
          placeholder="e.g., Dr. Wilson"
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="status">Status</Label>
        <Select
          value={formData.status || 'Pending'}
          onValueChange={(value) => handleChange('status', value)}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Pending">Pending</SelectItem>
            <SelectItem value="Confirmed">Confirmed</SelectItem>
            <SelectItem value="Completed">Completed</SelectItem>
            <SelectItem value="Cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit">
          {appointment ? 'Update' : 'Create'} Appointment
        </Button>
      </DialogFooter>
    </form>
  );
});
