/**
 * Main Dashboard Component
 *
 * Comprehensive dashboard showing:
 * - Life score overview
 * - Recent events
 * - Predictions (energy, mood)
 * - AI insights
 * - Timeline visualization
 */

'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ChartBarIcon,
  BoltIcon,
  FaceSmileIcon,
  SparklesIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline';

import { EnergyChart } from '../charts/EnergyChart';
import { MoodChart } from '../charts/MoodChart';
import { TimelineView } from '../charts/TimelineView';
import { InsightCard } from './InsightCard';
import { QuickActions } from './QuickActions';
import { api } from '@/lib/api';

export function Dashboard() {
  const [timeRange, setTimeRange] = useState('7d');

  // Fetch dashboard data
  const { data: predictions, isLoading: predictionsLoading } = useQuery({
    queryKey: ['predictions'],
    queryFn: async () => {
      const [energy, mood] = await Promise.all([
        api.predictions.energy(),
        api.predictions.mood(),
      ]);
      return { energy, mood };
    },
  });

  const { data: insights, isLoading: insightsLoading } = useQuery({
    queryKey: ['insights'],
    queryFn: () => api.insights.list({ page: 1, page_size: 5 }),
  });

  const { data: timeline, isLoading: timelineLoading } = useQuery({
    queryKey: ['timeline', timeRange],
    queryFn: () => api.timeline.get(parseInt(timeRange)),
  });

  const { data: recentEvents } = useQuery({
    queryKey: ['events', 'recent'],
    queryFn: () => api.events.list({ page: 1, page_size: 10 }),
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">
              Your Life Dashboard
            </h1>
            <div className="flex space-x-2">
              {['7d', '30d', '90d'].map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-3 py-1 rounded-md text-sm font-medium ${
                    timeRange === range
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Prediction Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Energy Prediction */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <BoltIcon className="h-6 w-6 text-yellow-500 mr-2" />
                <h2 className="text-lg font-semibold text-gray-900">
                  Energy Prediction
                </h2>
              </div>
              {predictionsLoading && (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-600" />
              )}
            </div>

            {predictions?.energy && (
              <div>
                <div className="flex items-baseline mb-2">
                  <span className="text-4xl font-bold text-gray-900">
                    {predictions.energy.prediction.toFixed(1)}
                  </span>
                  <span className="text-lg text-gray-500 ml-1">/10</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                  <div
                    className="bg-yellow-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${predictions.energy.prediction * 10}%` }}
                  />
                </div>
                <p className="text-sm text-gray-600">
                  Confidence: {(predictions.energy.confidence * 100).toFixed(0)}%
                </p>
              </div>
            )}
          </div>

          {/* Mood Prediction */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <FaceSmileIcon className="h-6 w-6 text-blue-500 mr-2" />
                <h2 className="text-lg font-semibold text-gray-900">
                  Mood Prediction
                </h2>
              </div>
              {predictionsLoading && (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-600" />
              )}
            </div>

            {predictions?.mood && (
              <div>
                <div className="text-3xl font-bold text-gray-900 mb-2 capitalize">
                  {predictions.mood.prediction_class.replace('_', ' ')}
                </div>
                <div className="space-y-2 mb-3">
                  {Object.entries(predictions.mood.class_probabilities || {}).map(
                    ([mood, prob]: [string, any]) => (
                      <div key={mood} className="flex items-center">
                        <span className="text-xs text-gray-600 w-24 capitalize">
                          {mood.replace('_', ' ')}
                        </span>
                        <div className="flex-1 bg-gray-200 rounded-full h-1.5 ml-2">
                          <div
                            className="bg-blue-500 h-1.5 rounded-full"
                            style={{ width: `${prob * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500 ml-2 w-10 text-right">
                          {(prob * 100).toFixed(0)}%
                        </span>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Energy Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Energy Trends
            </h2>
            {!timelineLoading && timeline && (
              <EnergyChart data={timeline} />
            )}
          </div>

          {/* Mood Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Mood Trends
            </h2>
            {!timelineLoading && timeline && (
              <MoodChart data={timeline} />
            )}
          </div>
        </div>

        {/* Timeline and Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Timeline */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
            <div className="flex items-center mb-4">
              <CalendarIcon className="h-6 w-6 text-indigo-600 mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">
                Your Timeline
              </h2>
            </div>
            {!timelineLoading && timeline && (
              <TimelineView data={timeline} />
            )}
          </div>

          {/* AI Insights */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <SparklesIcon className="h-6 w-6 text-purple-600 mr-2" />
                <h2 className="text-lg font-semibold text-gray-900">
                  AI Insights
                </h2>
              </div>
            </div>

            {insightsLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
                    <div className="h-3 bg-gray-200 rounded w-full" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {insights?.items.slice(0, 5).map((insight: any) => (
                  <InsightCard key={insight.id} insight={insight} />
                ))}
              </div>
            )}

            <button
              className="mt-4 w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors text-sm font-medium"
              onClick={() => {
                // Generate new insights
              }}
            >
              Generate New Insights
            </button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8">
          <QuickActions />
        </div>
      </main>
    </div>
  );
}
