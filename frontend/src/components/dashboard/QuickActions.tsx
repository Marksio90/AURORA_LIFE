/**
 * Quick Actions Component
 * Fast access buttons for common user actions
 */

'use client';

import {
  PlusCircleIcon,
  SparklesIcon,
  ChartBarIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';

interface QuickAction {
  id: string;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  action: () => void;
}

export function QuickActions() {
  const actions: QuickAction[] = [
    {
      id: 'add-event',
      label: 'Log Life Event',
      description: 'Record a new activity or moment',
      icon: PlusCircleIcon,
      color: 'bg-blue-500 hover:bg-blue-600',
      action: () => {
        // TODO: Open modal to add event
        console.log('Add event');
      },
    },
    {
      id: 'generate-insights',
      label: 'Generate Insights',
      description: 'Get AI-powered recommendations',
      icon: SparklesIcon,
      color: 'bg-purple-500 hover:bg-purple-600',
      action: () => {
        // TODO: Trigger AI analysis
        console.log('Generate insights');
      },
    },
    {
      id: 'view-analytics',
      label: 'View Analytics',
      description: 'Deep dive into your patterns',
      icon: ChartBarIcon,
      color: 'bg-green-500 hover:bg-green-600',
      action: () => {
        // TODO: Navigate to analytics page
        console.log('View analytics');
      },
    },
    {
      id: 'settings',
      label: 'Settings',
      description: 'Manage your preferences',
      icon: Cog6ToothIcon,
      color: 'bg-gray-500 hover:bg-gray-600',
      action: () => {
        // TODO: Navigate to settings
        console.log('Settings');
      },
    },
  ];

  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.id}
              onClick={action.action}
              className="flex flex-col items-center justify-center p-6 bg-white rounded-lg shadow hover:shadow-lg transition-all group"
            >
              <div
                className={`${action.color} p-3 rounded-full text-white mb-3 group-hover:scale-110 transition-transform`}
              >
                <Icon className="h-6 w-6" />
              </div>

              <h3 className="text-sm font-semibold text-gray-900 mb-1">
                {action.label}
              </h3>

              <p className="text-xs text-gray-500 text-center">
                {action.description}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
