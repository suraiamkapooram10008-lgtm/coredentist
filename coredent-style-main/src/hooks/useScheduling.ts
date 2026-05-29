export function useScheduling() {
  return {
    appointments: [],
    isLoading: false,
    error: null,
    refetch: () => {},
    loadData: () => {},
    selectedDate: new Date(),
    viewMode: 'day',
    setSelectedDate: () => {},
    setViewMode: () => {},
    createAppointment: () => Promise.resolve(),
    updateAppointment: () => Promise.resolve(),
    deleteAppointment: () => Promise.resolve(),
  };
}
