import React from 'react';
import { PieChart, Pie, Cell } from 'recharts';
import { BaseChart, ChartTooltip } from './BaseChart';

interface AppointmentPieChartProps {
  data: {
    type: string;
    count: number;
  }[];
  colors: string[];
}

export const AppointmentPieChart = React.memo(({ data, colors }: AppointmentPieChartProps) => {
  return (
    <BaseChart 
      title="Appointments by Type" 
      description="Distribution of appointment types" 
      data={data}
    >
      <PieChart>
        <Pie
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
          dataKey="count"
          nameKey="type"
          label={({ type, percent }) => `${type} ${(percent * 100).toFixed(0)}%`}
          labelLine={false}
          data={data}
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
          ))}
        </Pie>
        <ChartTooltip />
      </PieChart>
    </BaseChart>
  );
});

AppointmentPieChart.displayName = 'AppointmentPieChart';
