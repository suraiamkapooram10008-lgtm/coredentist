import React from 'react';
import { BarChart, Bar, Legend } from 'recharts';
import { BaseChart, ChartGrid, ChartXAxis, ChartYAxis, ChartTooltip } from './BaseChart';

interface RevenueChartProps {
  data: {
    month: string;
    revenue: number;
    collected: number;
  }[];
  formatCurrency: (amount: number) => string;
}

export const RevenueChart = React.memo(({ data, formatCurrency }: RevenueChartProps) => {
  return (
    <BaseChart 
      title="Revenue Trend" 
      description="Monthly revenue vs collected" 
      data={data}
    >
      <BarChart>
        <ChartGrid />
        <ChartXAxis dataKey="month" />
        <ChartYAxis formatter={(v) => `$${v / 1000}k`} />
        <ChartTooltip formatter={(value: number) => formatCurrency(value)} />
        <Legend />
        <Bar dataKey="revenue" name="Revenue" fill="hsl(var(--chart-1))" radius={[4, 4, 0, 0]} />
        <Bar dataKey="collected" name="Collected" fill="hsl(var(--chart-2))" radius={[4, 4, 0, 0]} />
      </BarChart>
    </BaseChart>
  );
});

RevenueChart.displayName = 'RevenueChart';
