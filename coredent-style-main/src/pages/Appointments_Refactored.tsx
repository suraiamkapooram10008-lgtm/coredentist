/**
 * Appointments Page (Refactored)
 * Detailed appointment management with modular components
 */

import React, { useState, useMemo } from 'react';
import { logger } from '@/lib/logger';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Plus, Search, Calendar } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  useAppointments,
  useAppointmentTypes,
  useCreateAppointment,
  useUpdateAppointment,
  useDeleteAppointment,
  useSendAppointmentReminder,
} from '@/hooks/useAppointments';
import type { Appointment } from '@/services/appointmentsApi';

// Custom hooks
import { useAppointmentStats } from '@/hooks/useAppointmentStats';
import { useAppointmentFilters } from '@/hooks/useAppointmentFilters';

// Components
import { AppointmentStatCard } from '@/components/appointments/AppointmentStatCard';
import { AppointmentListView } from '@/components/appointments/AppointmentListView';
import { AppointmentTimelineView } from '@/components/appointments/AppointmentTimelineView';
import { AppointmentTypesView } from '@/components/appointments/AppointmentTypesView';
import { AppointmentForm } from '@/components/appointments/AppointmentForm';

/**
 * Appointments Page Component
 */
export default function Appointments() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [showForm, setShowForm] = useState(false);
  const [selectedAppointment, setSelectedAppointment] =
    useState<Appointment | null>(null);
  const { toast } = useToast();

  // Fetch data
  const { data: appointmentsData, isLoading: appointmentsLoading } =
    useAppointments({
      date: selectedDate,
      search: searchTerm || undefined,
    });

  const { data: typesData } = useAppointmentTypes();

  const appointments = appointmentsData?.data?.appointments ?? [];
  const appointmentTypes = typesData?.data?.types ?? [];

  // Calculate stats
  const stats = useAppointmentStats(appointments);

  // Filter appointments
  const filteredAppointments = useAppointmentFilters(appointments, {
    searchTerm,
  });

  // Mutations
  const createMutation = useCreateAppointment({
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'Appointment created successfully',
      });
      setShowForm(false);
      setSelectedAppointment(null);
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to create appointment',
        variant: 'destructive',
      });
    },
  });

  const updateMutation = useUpdateAppointment({
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'Appointment updated successfully',
      });
      setShowForm(false);
      setSelectedAppointment(null);
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to update appointment',
        variant: 'destructive',
      });
    },
  });

  const deleteMutation = useDeleteAppointment({
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'Appointment deleted successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to delete appointment',
        variant: 'destructive',
      });
    },
  });

  const reminderMutation = useSendAppointmentReminder({
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'Reminder sent successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to send reminder',
        variant: 'destructive',
      });
    },
  });

  // Handlers
  const handleNewAppointment = () => {
    setSelectedAppointment(null);
    setShowForm(true);
  };

  const handleEditAppointment = (apt: Appointment) => {
    setSelectedAppointment(apt);
    setShowForm(true);
  };

  const handleFormSubmit = (data: Partial<Appointment>) => {
    logger.info('Appointment form submitted', { data });
    if (selectedAppointment?.id) {
      updateMutation.mutate({ id: selectedAppointment.id, data });
    } else {
      createMutation.mutate(data as Omit<Appointment, 'id'>);
    }
  };

  const handleFormCancel = () => {
    setShowForm(false);
    setSelectedAppointment(null);
  };

  const handleDelete = (id: string) => {
    if (window.confirm('Are you sure you want to delete this appointment?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleSendReminder = (id: string) => {
    reminderMutation.mutate(id);
  };

  // Stat cards configuration
  const statCards = useMemo(
    () => [
      {
        title: "Today's Appointments",
        value: stats.todayAppointments,
        icon: Calendar,
        color: 'text-muted-foreground',
      },
      {
        title: 'Confirmed',
        value: stats.confirmed,
        icon: Calendar,
        color: 'text-green-500',
      },
      {
        title: 'Pending',
        value: stats.pending,
        icon: Calendar,
        color: 'text-yellow-500',
      },
      {
        title: 'Cancelled',
        value: stats.cancelled,
        icon: Calendar,
        color: 'text-red-500',
      },
    ],
    [stats]
  );

  return (
    <div className="container mx-auto py-6 space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Appointments</h1>
          <p className="text-muted-foreground">Manage all patient appointments</p>
        </div>
        <Button onClick={handleNewAppointment}>
          <Plus className="mr-2 h-4 w-4" />
          New Appointment
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 stagger-fade-in">
        {statCards.map((stat) => (
          <AppointmentStatCard
            key={stat.title}
            title={stat.title}
            value={stat.value}
            icon={stat.icon}
            color={stat.color}
            isLoading={appointmentsLoading}
          />
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <Input
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="w-auto"
        />
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search appointments..."
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="list" className="space-y-4">
        <TabsList>
          <TabsTrigger value="list">List View</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="types">Appointment Types</TabsTrigger>
        </TabsList>

        <TabsContent value="list">
          <AppointmentListView
            appointments={filteredAppointments}
            isLoading={appointmentsLoading}
            onEdit={handleEditAppointment}
            onSendReminder={handleSendReminder}
            onDelete={handleDelete}
          />
        </TabsContent>

        <TabsContent value="timeline">
          <AppointmentTimelineView
            appointments={filteredAppointments}
            isLoading={appointmentsLoading}
          />
        </TabsContent>

        <TabsContent value="types">
          <AppointmentTypesView types={appointmentTypes} />
        </TabsContent>
      </Tabs>

      {/* Appointment Form Dialog */}
      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {selectedAppointment ? 'Edit Appointment' : 'New Appointment'}
            </DialogTitle>
            <DialogDescription>
              {selectedAppointment
                ? 'Update the appointment details'
                : 'Create a new appointment'}
            </DialogDescription>
          </DialogHeader>
          <AppointmentForm
            appointment={selectedAppointment}
            appointmentTypes={appointmentTypes}
            onSubmit={handleFormSubmit}
            onCancel={handleFormCancel}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
