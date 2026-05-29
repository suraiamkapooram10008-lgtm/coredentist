import type { Appointment } from '@/services/appointmentsApi';

interface AppointmentListViewProps {
  appointments?: Appointment[];
  isLoading?: boolean;
}

export function AppointmentListView({ appointments, isLoading }: AppointmentListViewProps) {
  if (isLoading) return <div>Loading appointments...</div>;
  if (!appointments?.length) return <div>No appointments found</div>;
  return (
    <div>
      {appointments.map((apt) => (
        <div key={apt.id}>{apt.patient || apt.patientName}</div>
      ))}
    </div>
  );
}
