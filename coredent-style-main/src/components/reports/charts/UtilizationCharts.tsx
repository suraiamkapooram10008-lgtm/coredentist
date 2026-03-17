import React from 'react';
import { 
  BarChart, 
  Bar, 
  CartesianGrid, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface UtilizationChartsProps {
  peakHours: {
    hour: string;
    utilization: number;
  }[];
  byChair: {
    chair: string;
    utilization: number;
    appointments: number;
  }[];
  byDayOfWeek: {
    day: string;
    utilization: number;
  }[];
}

export const UtilizationCharts = React.memo(({ peakHours, byChair, byDayOfWeek }: UtilizationChartsProps) => {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Hourly Utilization</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={peakHours}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="hour" />
                <YAxis tickFormatter={(v) => `${v}%`} />
                <Tooltip
                  formatter={(value: number) => `${value}%`}
                  contentStyle={{
                    backgroundColor: 'hsl(var(--background))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="utilization" name="Utilization" fill="hsl(var(--chart-3))" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Chair Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {byChair.map((chair) => (
              <div key={chair.chair} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{chair.chair}</span>
                  <div className="flex items-center gap-4">
                    <span className="text-muted-foreground">
                      {chair.appointments} appts
                    </span>
                    <span className={cn(
                      'font-medium',
                      chair.utilization >= 70 ? 'text-green-600' :
                        chair.utilization >= 50 ? 'text-amber-600' : 'text-red-600'
                    )}>
                      {chair.utilization}%
                    </span>
                  </div>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className={cn(
                      'h-full rounded-full transition-all',
                      chair.utilization >= 70 ? 'bg-green-500' :
                        chair.utilization >= 50 ? 'bg-amber-500' : 'bg-red-500'
                    )}
                    style={{ width: `${chair.utilization}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Utilization by Day of Week</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byDayOfWeek} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis type="number" tickFormatter={(v) => `${v}%`} />
                <YAxis dataKey="day" type="category" width={40} />
                <Tooltip
                  formatter={(value: number) => `${value}%`}
                  contentStyle={{
                    backgroundColor: 'hsl(var(--background))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="utilization" name="Utilization" fill="hsl(var(--chart-4))" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
});

UtilizationCharts.displayName = 'UtilizationCharts';
