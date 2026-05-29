export function useAppointments(_params?: { date?: string; search?: string }) {
  return {
    data: {
      data: {
        appointments: [
          { id: 'apt-1', patientName: 'John Doe', time: '10:00 AM', status: 'scheduled', type: 'checkup', dentist: 'Dr. Smith', duration: '60' },
          { id: 'apt-2', patientName: 'Jane Smith', time: '2:00 PM', status: 'scheduled', type: 'cleaning', dentist: 'Dr. Smith', duration: '60' },
        ],
      },
    },
    isLoading: false,
    isPending: false,
    refetch: () => {},
    error: null,
  };
}

export function useAppointmentStats() {
  return {
    data: {
      data: {
        todayAppointments: 2,
        confirmed: 1,
        pending: 1,
        cancelled: 0,
      },
    },
    isLoading: false,
  };
}

export function useAppointmentTypes() {
  return {
    data: {
      data: {
        types: [
          { id: '1', name: 'Checkup', duration: 30 },
          { id: '2', name: 'Cleaning', duration: 45 },
          { id: '3', name: 'Root Canal', duration: 60 },
        ],
      },
    },
    isLoading: false,
  };
}

export function useCreateAppointment(_config?: { onSuccess?: () => void; onError?: () => void }) {
  return { mutate: () => {}, isPending: false };
}

export function useUpdateAppointment(_config?: { onSuccess?: () => void; onError?: () => void }) {
  return { mutate: () => {}, isPending: false };
}

export function useDeleteAppointment(_config?: { onSuccess?: () => void; onError?: () => void }) {
  return { mutate: () => {}, isPending: false };
}

export function useSendAppointmentReminder(_config?: { onSuccess?: () => void; onError?: () => void }) {
  return { mutate: () => {}, isPending: false };
}
