/**
 * Timeline Visualization Component
 * Displays chronological life events with impact indicators
 */

'use client';

import { format, parseISO } from 'date-fns';
import type { TimelineResponse } from '@/types/api';

interface TimelineViewProps {
  data: TimelineResponse;
}

export function TimelineView({ data }: TimelineViewProps) {
  if (!data.entries || data.entries.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No events to display</p>
        <p className="text-sm text-gray-400 mt-2">
          Start logging your life events to see your timeline
        </p>
      </div>
    );
  }

  const getImpactColor = (impact?: number) => {
    if (!impact) return 'bg-gray-400';
    if (impact > 0.7) return 'bg-green-500';
    if (impact > 0.4) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, string> = {
      physical: '💪',
      mental: '🧠',
      social: '👥',
      professional: '💼',
      personal: '🌟',
    };
    return icons[category] || '📝';
  };

  return (
    <div className="relative">
      {/* Timeline line */}
      <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-200" />

      {/* Events */}
      <div className="space-y-6">
        {data.entries.map((entry) => (
          <div key={entry.id} className="relative pl-16">
            {/* Timeline dot */}
            <div className="absolute left-6 -ml-2.5 mt-1.5">
              <div
                className={`w-5 h-5 rounded-full border-2 border-white ${getImpactColor(
                  entry.impact_score
                )}`}
              />
            </div>

            {/* Event card */}
            <div className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-xl">
                      {getCategoryIcon(entry.event_category)}
                    </span>
                    <h4 className="text-sm font-semibold text-gray-900">
                      {entry.title}
                    </h4>
                    <span className="text-xs text-gray-500 capitalize">
                      {entry.event_type}
                    </span>
                  </div>

                  <p className="text-xs text-gray-600">
                    {format(parseISO(entry.event_time), 'MMM d, yyyy • h:mm a')}
                  </p>

                  {/* Impact indicators */}
                  {(entry.energy_impact !== undefined ||
                    entry.mood_impact !== undefined) && (
                    <div className="mt-2 flex items-center space-x-4 text-xs">
                      {entry.energy_impact !== undefined && (
                        <div className="flex items-center">
                          <span className="text-gray-500 mr-1">Energy:</span>
                          <span
                            className={
                              entry.energy_impact > 0
                                ? 'text-green-600'
                                : 'text-red-600'
                            }
                          >
                            {entry.energy_impact > 0 ? '+' : ''}
                            {(entry.energy_impact * 100).toFixed(0)}%
                          </span>
                        </div>
                      )}

                      {entry.mood_impact !== undefined && (
                        <div className="flex items-center">
                          <span className="text-gray-500 mr-1">Mood:</span>
                          <span
                            className={
                              entry.mood_impact > 0
                                ? 'text-green-600'
                                : 'text-red-600'
                            }
                          >
                            {entry.mood_impact > 0 ? '+' : ''}
                            {(entry.mood_impact * 100).toFixed(0)}%
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary footer */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <p className="text-sm text-gray-600">
          Showing <span className="font-semibold">{data.entries.length}</span> of{' '}
          <span className="font-semibold">{data.total_events}</span> events from
          the last {data.period_days} days
        </p>
      </div>
    </div>
  );
}
