import React from 'react';
import { format, parseISO } from 'date-fns';
import { Calendar, Clock, FileText } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import type { PatientRecord } from '@/types/patient';

interface PatientQuickStatsProps {
  stats: PatientRecord['appointmentStats'];
  notesCount: number;
}

export const PatientQuickStats = React.memo(({ stats, notesCount }: PatientQuickStatsProps) => {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Calendar className="h-5 w-5 text-primary" />
            </div>
            <div>
              <div className="text-2xl font-bold">{stats.total}</div>
              <div className="text-sm text-muted-foreground">Total Visits</div>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
              <Clock className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <div className="text-sm font-medium">
                {stats.lastVisit 
                  ? format(parseISO(stats.lastVisit), 'MMM d, yyyy')
                  : 'Never'
                }
              </div>
              <div className="text-sm text-muted-foreground">Last Visit</div>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
              <Calendar className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <div className="text-sm font-medium">
                {stats.nextAppointment 
                  ? format(parseISO(stats.nextAppointment), 'MMM d, yyyy')
                  : 'Not scheduled'
                }
              </div>
              <div className="text-sm text-muted-foreground">Next Appt</div>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
              <FileText className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <div className="text-2xl font-bold">{notesCount}</div>
              <div className="text-sm text-muted-foreground">Notes</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
});

PatientQuickStats.displayName = 'PatientQuickStats';
