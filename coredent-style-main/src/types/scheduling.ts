export interface ScheduleAppointment {
  id: string;
  patientName: string;
  time: string;
  duration: string;
  type: string;
  status: string;
  dentist: string;
}

export interface AppointmentFormData {
  patientName: string;
  time: string;
  duration: string;
  type: string;
  dentist: string;
}

export interface PatientSearchResult {
  id: string;
  name: string;
  phone: string;
}

export function parseTimeString(time: string): string {
  return time;
}
