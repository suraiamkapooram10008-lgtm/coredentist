// ============================================
// Appointment History Component
// Shows patient's past and upcoming appointments
// ============================================

import { useState, useEffect } from 'react';
import { format, parseISO } from 'date-fns';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Calendar, 
  Clock, 
  User,
  CheckCircle2,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { patientApi } from '@/services/patientApi';

interface AppointmentHistoryProps {
  patientId: string;
}

interface AppointmentHistoryItem {
  id: string;
  date: string;
  type: string;
  provider: string;
  status: string;
}

const statusConfig: Record<string, { icon: React.ComponentType<{ className?: string }>; color: string }> = {
  completed: { icon: CheckCircle2, color: 'text-green-600' },
  cancelled: { icon: XCircle, color: 'text-red-600' },
  no_show: { icon: AlertCircle, color: 'text-amber-600' },
  scheduled: { icon: Clock, color: 'text-blue-600' },
  confirmed: { icon: CheckCircle2, color: 'text-blue-600' },
};

export function AppointmentHistory({ patientId }: AppointmentHistoryProps) {
  const navigate = useNavigate();
  const [appointments, setAppointments] = useState<AppointmentHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadAppointments = async () => {
      setIsLoading(true);
      try {
        const data = await patientApi.getAppointmentHistory(patientId);
        setAppointments(data);
      } catch {
        // Failed to load appointments - will show empty state
      } finally {
        setIsLoading(false);
      }
    };

    loadAppointments();
  }, [patientId]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Appointment History</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  const upcomingAppointments = appointments.filter(
    a => new Date(a.date) >= new Date() && !['cancelled', 'no_show', 'completed'].includes(a.status)
  );
  const pastAppointments = appointments.filter(
    a => new Date(a.date) < new Date() || ['cancelled', 'no_show', 'completed'].includes(a.status)
  );

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Appointment History</CardTitle>
        <Button onClick={() => navigate('/schedule')} className="gap-2">
          <Calendar className="h-4 w-4" />
          Schedule New
        </Button>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="all">
          <TabsList>
            <TabsTrigger value="all">All ({appointments.length})</TabsTrigger>
            <TabsTrigger value="upcoming">Upcoming ({upcomingAppointments.length})</TabsTrigger>
            <TabsTrigger value="past">Past ({pastAppointments.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="mt-4">
            <AppointmentList appointments={appointments} />
          </TabsContent>

          <TabsContent value="upcoming" className="mt-4">
            {upcomingAppointments.length > 0 ? (
              <AppointmentList appointments={upcomingAppointments} />
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Calendar className="h-12 w-12 mx-auto mb-2 opacity-30" />
                <p>No upcoming appointments</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="past" className="mt-4">
            {pastAppointments.length > 0 ? (
              <AppointmentList appointments={pastAppointments} />
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Calendar className="h-12 w-12 mx-auto mb-2 opacity-30" />
                <p>No past appointments</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

function AppointmentList({ appointments }: { appointments: AppointmentHistoryItem[] }) {
  return (
    <div className="space-y-3">
      {appointments.map((appointment) => {
        const config = statusConfig[appointment.status] || statusConfig.scheduled;
        const StatusIcon = config.icon;

        return (
          <div
            key={appointment.id}
            className="flex items-center justify-between p-4 rounded-lg border hover:bg-muted/50 transition-colors"
          >
            <div className="flex items-center gap-4">
              <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                <Calendar className="h-5 w-5 text-primary" />
              </div>
              <div>
                <div className="font-medium">{appointment.type}</div>
                <div className="flex items-center gap-3 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {format(parseISO(appointment.date), 'MMM d, yyyy')}
                  </span>
                  <span className="flex items-center gap-1">
                    <User className="h-3 w-3" />
                    {appointment.provider}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <StatusIcon className={`h-4 w-4 ${config.color}`} />
              <Badge variant="outline" className="capitalize">
                {appointment.status.replace('_', ' ')}
              </Badge>
            </div>
          </div>
        );
      })}
    </div>
  );
}
