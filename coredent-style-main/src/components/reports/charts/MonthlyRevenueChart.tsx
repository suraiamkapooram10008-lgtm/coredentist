import React from 'react';
import { LineChart, Line, Legend } from 'recharts';
import { BaseChart, ChartGrid, ChartXAxis, ChartYAxis, ChartTooltip } from './BaseChart';

interface MonthlyRevenueChartProps {
  data: {
    month: string;
    revenue: number;
    collected: number;
  }[];
  formatCurrency: (amount: number) => string;
}

export const MonthlyRevenueChart = React.memo(({ data, formatCurrency }: MonthlyRevenueChartProps) => {
  return (
    <BaseChart title="Monthly Revenue" data={data}>
      <LineChart>
        <ChartGrid />
        <ChartXAxis dataKey="month" />
        <ChartYAxis formatter={(v) => `$${v / 1000}k`} />
        <ChartTooltip formatter={(value: number) => formatCurrency(value)} />
        <Legend />
        <Line type="monotone" dataKey="revenue" name="Revenue" stroke="hsl(var(--chart-1))" strokeWidth={2} />
        <Line type="monotone" dataKey="collected" name="Collected" stroke="hsl(var(--chart-2))" strokeWidth={2} />
      </LineChart>
    </BaseChart>
  );
});

MonthlyRevenueChart.displayName = 'MonthlyRevenueChart';
