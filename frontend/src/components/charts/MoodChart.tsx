/**
 * Mood Trends Chart Component
 *
 * Displays mood distribution and trends over time
 */

'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';
import { format } from 'date-fns';

interface MoodChartProps {
  data: any[];
}

const MOOD_COLORS: Record<string, string> = {
  very_positive: '#10b981',
  positive: '#34d399',
  neutral: '#fbbf24',
  negative: '#fb923c',
  very_negative: '#ef4444',
};

export function MoodChart({ data }: MoodChartProps) {
  // Transform data for chart
  const chartData = data.map((day) => {
    const moodCounts = day.event_counts?.mood || {};
    return {
      date: format(new Date(day.date), 'MMM dd'),
      ...moodCounts,
    };
  });

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
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
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#ffffff',
            border: '1px solid #e5e7eb',
            borderRadius: '0.5rem',
          }}
        />
        <Legend />
        <Bar dataKey="very_positive" stackId="mood" fill={MOOD_COLORS.very_positive} name="Very Positive" />
        <Bar dataKey="positive" stackId="mood" fill={MOOD_COLORS.positive} name="Positive" />
        <Bar dataKey="neutral" stackId="mood" fill={MOOD_COLORS.neutral} name="Neutral" />
        <Bar dataKey="negative" stackId="mood" fill={MOOD_COLORS.negative} name="Negative" />
        <Bar dataKey="very_negative" stackId="mood" fill={MOOD_COLORS.very_negative} name="Very Negative" />
      </BarChart>
    </ResponsiveContainer>
  );
}
