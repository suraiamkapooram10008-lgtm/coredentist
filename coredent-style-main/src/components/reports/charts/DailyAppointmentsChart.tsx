import React from 'react';
import { BarChart, Bar } from 'recharts';
import { BaseChart, ChartGrid, ChartXAxis, ChartYAxis, ChartTooltip } from './BaseChart';

interface DailyAppointmentsChartProps {
  data: {
    day: string;
    count: number;
  }[];
}

export const DailyAppointmentsChart = React.memo(({ data }: DailyAppointmentsChartProps) => {
  return (
    <BaseChart title="Daily Appointments (Last 7 Days)" data={data}>
      <BarChart>
        <ChartGrid />
        <ChartXAxis dataKey="day" />
        <ChartYAxis />
        <ChartTooltip />
        <Bar dataKey="count" name="Appointments" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
      </BarChart>
    </BaseChart>
  );
});

DailyAppointmentsChart.displayName = 'DailyAppointmentsChart';
