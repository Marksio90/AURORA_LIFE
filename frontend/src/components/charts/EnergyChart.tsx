/**
 * Energy Levels Chart Component
 *
 * Displays energy levels over time with Recharts
 */

'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { format } from 'date-fns';

interface EnergyChartProps {
  data: any[];
}

export function EnergyChart({ data }: EnergyChartProps) {
  // Transform data for chart
  const chartData = data.map((day) => ({
    date: format(new Date(day.date), 'MMM dd'),
    energy: day.metrics?.avg_energy || 0,
    prediction: day.metrics?.predicted_energy || 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={chartData}>
        <defs>
          <linearGradient id="colorEnergy" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="date"
          stroke="#6b7280"
          fontSize={12}
          tickLine={false}
        />
        <YAxis
          stroke="#6b7280"
          fontSize={12}
          tickLine={false}
          domain={[0, 10]}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#ffffff',
            border: '1px solid #e5e7eb',
            borderRadius: '0.5rem',
          }}
        />
        <Area
          type="monotone"
          dataKey="energy"
          stroke="#f59e0b"
          strokeWidth={2}
          fillOpacity={1}
          fill="url(#colorEnergy)"
          name="Actual Energy"
        />
        <Line
          type="monotone"
          dataKey="prediction"
          stroke="#10b981"
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={false}
          name="Predicted"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
