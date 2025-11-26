/**
 * AI Insight Card Component
 * Displays individual AI-generated insights
 */

'use client';

import { format, parseISO } from 'date-fns';
import type { AIInsight } from '@/types/api';
import {
  ExclamationTriangleIcon,
  InformationCircleIcon,
  LightBulbIcon,
} from '@heroicons/react/24/outline';

interface InsightCardProps {
  insight: AIInsight;
  onClick?: () => void;
}

export function InsightCard({ insight, onClick }: InsightCardProps) {
  const getPriorityStyles = (priority: string) => {
    switch (priority) {
      case 'high':
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          text: 'text-red-700',
          icon: <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />,
        };
      case 'medium':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200',
          text: 'text-yellow-700',
          icon: <LightBulbIcon className="h-5 w-5 text-yellow-500" />,
        };
      case 'low':
      default:
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          text: 'text-blue-700',
          icon: <InformationCircleIcon className="h-5 w-5 text-blue-500" />,
        };
    }
  };

  const styles = getPriorityStyles(insight.priority);

  return (
    <div
      className={`${styles.bg} ${styles.border} border rounded-lg p-3 cursor-pointer hover:shadow-md transition-shadow`}
      onClick={onClick}
    >
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0 mt-0.5">{styles.icon}</div>

        <div className="flex-1 min-w-0">
          <h4 className={`text-sm font-semibold ${styles.text} mb-1`}>
            {insight.title}
          </h4>

          <p className="text-sm text-gray-700 line-clamp-2">{insight.content}</p>

          <div className="mt-2 flex items-center justify-between">
            <span className="text-xs text-gray-500 capitalize">
              {insight.category}
            </span>
            <span className="text-xs text-gray-400">
              {format(parseISO(insight.created_at), 'MMM d')}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
