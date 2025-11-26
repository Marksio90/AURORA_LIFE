/**
 * Home Page
 */

import Link from 'next/link';
import {
  SparklesIcon,
  ChartBarIcon,
  BoltIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';

export default function HomePage() {
  const features = [
    {
      name: 'AI-Powered Insights',
      description: 'Get personalized recommendations based on your life patterns',
      icon: SparklesIcon,
    },
    {
      name: 'Predictive Analytics',
      description: 'Forecast your energy and mood to plan your day better',
      icon: ChartBarIcon,
    },
    {
      name: 'Real-Time Tracking',
      description: 'Log events and see immediate impact on your well-being',
      icon: BoltIcon,
    },
    {
      name: 'Secure & Private',
      description: 'Your data is encrypted and never shared',
      icon: ShieldCheckIcon,
    },
  ];

  return (
    <div className="bg-white">
      {/* Hero */}
      <div className="relative isolate px-6 pt-14 lg:px-8">
        <div className="mx-auto max-w-2xl py-32 sm:py-48 lg:py-56">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
              Your Life, Optimized by AI
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              AURORA LIFE helps you make better decisions, predict your energy,
              and live your best life with AI-powered insights.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link
                href="/auth/register"
                className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
              >
                Get started
              </Link>
              <Link
                href="/auth/login"
                className="text-sm font-semibold leading-6 text-gray-900"
              >
                Sign in <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="mx-auto max-w-7xl px-6 lg:px-8 pb-24">
        <div className="mx-auto max-w-2xl lg:text-center">
          <h2 className="text-base font-semibold leading-7 text-indigo-600">
            Everything you need
          </h2>
          <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Features that transform your life
          </p>
        </div>
        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
          <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-4">
            {features.map((feature) => (
              <div key={feature.name} className="flex flex-col">
                <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-gray-900">
                  <feature.icon
                    className="h-5 w-5 flex-none text-indigo-600"
                    aria-hidden="true"
                  />
                  {feature.name}
                </dt>
                <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-600">
                  <p className="flex-auto">{feature.description}</p>
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </div>
  );
}
