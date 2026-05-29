import type { AppointmentType } from '@/services/appointmentsApi';

interface AppointmentTypesViewProps {
  types?: AppointmentType[];
}

export function AppointmentTypesView({ types }: AppointmentTypesViewProps) {
  return (
    <div>
      {types?.map((type) => (
        <div key={type.id}>{type.name}</div>
      ))}
    </div>
  );
}
