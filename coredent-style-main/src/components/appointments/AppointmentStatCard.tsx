export function AppointmentStatCard({ title, value, isLoading }: { title?: string; value?: number; isLoading?: boolean }) {
  if (isLoading) return <div>Loading...</div>;
  return (
    <div>
      <div>{title}</div>
      <div>{value ?? 0}</div>
    </div>
  );
}
