/**
 * User Onboarding Wizard
 *
 * Multi-step onboarding flow for new users:
 * 1. Welcome
 * 2. Profile setup
 * 3. Goals configuration
 * 4. Integration setup
 * 5. Preferences
 */
import { useState } from 'react';
import { useRouter } from 'next/router';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  component: React.ComponentType<StepProps>;
}

interface StepProps {
  onNext: (data: any) => void;
  onBack: () => void;
  data: any;
}

interface OnboardingData {
  profile?: {
    fullName: string;
    timezone: string;
    avatar?: string;
  };
  goals?: {
    primaryGoals: string[];
    customGoals: string[];
  };
  integrations?: {
    googleCalendar: boolean;
    fitbit: boolean;
  };
  preferences?: {
    theme: 'light' | 'dark' | 'auto';
    notifications: boolean;
    weeklyReports: boolean;
  };
}

// Step 1: Welcome
function WelcomeStep({ onNext }: StepProps) {
  return (
    <div className="text-center space-y-6">
      <div className="text-6xl">🌅</div>
      <h2 className="text-3xl font-bold">Welcome to Aurora Life</h2>
      <p className="text-gray-600 max-w-md mx-auto">
        Your personal life analytics platform. Let's get you set up in just a few steps.
      </p>
      <div className="grid grid-cols-3 gap-4 max-w-2xl mx-auto mt-8">
        <div className="p-4 bg-blue-50 rounded-lg">
          <div className="text-3xl mb-2">📊</div>
          <h3 className="font-semibold">Track</h3>
          <p className="text-sm text-gray-600">Monitor your daily activities</p>
        </div>
        <div className="p-4 bg-green-50 rounded-lg">
          <div className="text-3xl mb-2">🎯</div>
          <h3 className="font-semibold">Optimize</h3>
          <p className="text-sm text-gray-600">Get AI-powered insights</p>
        </div>
        <div className="p-4 bg-purple-50 rounded-lg">
          <div className="text-3xl mb-2">🚀</div>
          <h3 className="font-semibold">Grow</h3>
          <p className="text-sm text-gray-600">Achieve your goals</p>
        </div>
      </div>
      <button
        onClick={() => onNext({})}
        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition mt-8"
      >
        Get Started
      </button>
    </div>
  );
}

// Step 2: Profile Setup
function ProfileStep({ onNext, onBack, data }: StepProps) {
  const [profile, setProfile] = useState(data.profile || {
    fullName: '',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onNext({ profile });
  };

  return (
    <div className="max-w-md mx-auto space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold">Tell us about yourself</h2>
        <p className="text-gray-600 mt-2">We'll use this to personalize your experience</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Full Name</label>
          <input
            type="text"
            value={profile.fullName}
            onChange={(e) => setProfile({ ...profile, fullName: e.target.value })}
            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="John Doe"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Timezone</label>
          <select
            value={profile.timezone}
            onChange={(e) => setProfile({ ...profile, timezone: e.target.value })}
            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="America/New_York">Eastern Time</option>
            <option value="America/Chicago">Central Time</option>
            <option value="America/Denver">Mountain Time</option>
            <option value="America/Los_Angeles">Pacific Time</option>
            <option value="Europe/London">London</option>
            <option value="Europe/Paris">Paris</option>
            <option value="Asia/Tokyo">Tokyo</option>
            <option value="Australia/Sydney">Sydney</option>
          </select>
        </div>

        <div className="flex gap-3 pt-4">
          <button
            type="button"
            onClick={onBack}
            className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            Back
          </button>
          <button
            type="submit"
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Continue
          </button>
        </div>
      </form>
    </div>
  );
}

// Step 3: Goals Configuration
function GoalsStep({ onNext, onBack, data }: StepProps) {
  const [goals, setGoals] = useState(data.goals || {
    primaryGoals: [],
    customGoals: [],
  });

  const [customGoal, setCustomGoal] = useState('');

  const goalOptions = [
    { id: 'better_sleep', label: 'Improve Sleep Quality', icon: '😴' },
    { id: 'more_energy', label: 'Boost Energy Levels', icon: '⚡' },
    { id: 'productivity', label: 'Increase Productivity', icon: '📈' },
    { id: 'fitness', label: 'Get More Exercise', icon: '🏃' },
    { id: 'mindfulness', label: 'Practice Mindfulness', icon: '🧘' },
    { id: 'work_life_balance', label: 'Work-Life Balance', icon: '⚖️' },
  ];

  const toggleGoal = (goalId: string) => {
    setGoals({
      ...goals,
      primaryGoals: goals.primaryGoals.includes(goalId)
        ? goals.primaryGoals.filter(id => id !== goalId)
        : [...goals.primaryGoals, goalId],
    });
  };

  const addCustomGoal = () => {
    if (customGoal.trim()) {
      setGoals({
        ...goals,
        customGoals: [...goals.customGoals, customGoal.trim()],
      });
      setCustomGoal('');
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold">What are your goals?</h2>
        <p className="text-gray-600 mt-2">Select all that apply (you can change these later)</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {goalOptions.map((goal) => (
          <button
            key={goal.id}
            onClick={() => toggleGoal(goal.id)}
            className={`p-4 border-2 rounded-lg text-left transition ${
              goals.primaryGoals.includes(goal.id)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="text-2xl mb-2">{goal.icon}</div>
            <div className="font-medium">{goal.label}</div>
          </button>
        ))}
      </div>

      <div className="space-y-3">
        <label className="block text-sm font-medium">Custom Goals</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={customGoal}
            onChange={(e) => setCustomGoal(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addCustomGoal()}
            className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="Add your own goal..."
          />
          <button
            type="button"
            onClick={addCustomGoal}
            className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            Add
          </button>
        </div>
        {goals.customGoals.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {goals.customGoals.map((goal, idx) => (
              <span
                key={idx}
                className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm flex items-center gap-2"
              >
                {goal}
                <button
                  onClick={() => setGoals({
                    ...goals,
                    customGoals: goals.customGoals.filter((_, i) => i !== idx)
                  })}
                  className="text-blue-600 hover:text-blue-800"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="flex gap-3 pt-4">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
        >
          Back
        </button>
        <button
          type="button"
          onClick={() => onNext({ goals })}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Continue
        </button>
      </div>
    </div>
  );
}

// Step 4: Integrations
function IntegrationsStep({ onNext, onBack, data }: StepProps) {
  const [integrations, setIntegrations] = useState(data.integrations || {
    googleCalendar: false,
    fitbit: false,
  });

  const integrationOptions = [
    {
      id: 'googleCalendar',
      name: 'Google Calendar',
      description: 'Sync your calendar events',
      icon: '📅',
    },
    {
      id: 'fitbit',
      name: 'Fitbit',
      description: 'Track fitness and health data',
      icon: '⌚',
    },
  ];

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold">Connect Your Apps</h2>
        <p className="text-gray-600 mt-2">Optional integrations to enrich your data</p>
      </div>

      <div className="space-y-3">
        {integrationOptions.map((integration) => (
          <div
            key={integration.id}
            className="p-4 border rounded-lg flex items-center justify-between"
          >
            <div className="flex items-center gap-4">
              <div className="text-3xl">{integration.icon}</div>
              <div>
                <h3 className="font-semibold">{integration.name}</h3>
                <p className="text-sm text-gray-600">{integration.description}</p>
              </div>
            </div>
            <button
              onClick={() => setIntegrations({
                ...integrations,
                [integration.id]: !integrations[integration.id]
              })}
              className={`px-4 py-2 rounded-lg transition ${
                integrations[integration.id]
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              {integrations[integration.id] ? 'Connected' : 'Connect'}
            </button>
          </div>
        ))}
      </div>

      <div className="bg-blue-50 p-4 rounded-lg">
        <p className="text-sm text-blue-800">
          ℹ️ You can add more integrations later from your settings
        </p>
      </div>

      <div className="flex gap-3 pt-4">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
        >
          Back
        </button>
        <button
          type="button"
          onClick={() => onNext({ integrations })}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Continue
        </button>
      </div>
    </div>
  );
}

// Step 5: Preferences
function PreferencesStep({ onNext, onBack, data }: StepProps) {
  const [preferences, setPreferences] = useState(data.preferences || {
    theme: 'auto',
    notifications: true,
    weeklyReports: true,
  });

  const handleComplete = () => {
    onNext({ preferences });
  };

  return (
    <div className="max-w-md mx-auto space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold">Final Touches</h2>
        <p className="text-gray-600 mt-2">Customize your experience</p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Theme</label>
          <div className="grid grid-cols-3 gap-2">
            {(['light', 'dark', 'auto'] as const).map((theme) => (
              <button
                key={theme}
                onClick={() => setPreferences({ ...preferences, theme })}
                className={`py-2 px-4 rounded-lg border-2 transition capitalize ${
                  preferences.theme === theme
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                {theme}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <label className="flex items-center justify-between p-3 border rounded-lg">
            <span>Enable notifications</span>
            <input
              type="checkbox"
              checked={preferences.notifications}
              onChange={(e) => setPreferences({ ...preferences, notifications: e.target.checked })}
              className="w-5 h-5"
            />
          </label>

          <label className="flex items-center justify-between p-3 border rounded-lg">
            <span>Weekly summary reports</span>
            <input
              type="checkbox"
              checked={preferences.weeklyReports}
              onChange={(e) => setPreferences({ ...preferences, weeklyReports: e.target.checked })}
              className="w-5 h-5"
            />
          </label>
        </div>
      </div>

      <div className="flex gap-3 pt-4">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
        >
          Back
        </button>
        <button
          type="button"
          onClick={handleComplete}
          className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          Complete Setup
        </button>
      </div>
    </div>
  );
}

// Main Onboarding Wizard Component
export default function OnboardingWizard() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [onboardingData, setOnboardingData] = useState<OnboardingData>({});

  const steps: OnboardingStep[] = [
    {
      id: 'welcome',
      title: 'Welcome',
      description: 'Get started with Aurora Life',
      component: WelcomeStep,
    },
    {
      id: 'profile',
      title: 'Profile',
      description: 'Tell us about yourself',
      component: ProfileStep,
    },
    {
      id: 'goals',
      title: 'Goals',
      description: 'Set your objectives',
      component: GoalsStep,
    },
    {
      id: 'integrations',
      title: 'Integrations',
      description: 'Connect your apps',
      component: IntegrationsStep,
    },
    {
      id: 'preferences',
      title: 'Preferences',
      description: 'Customize your experience',
      component: PreferencesStep,
    },
  ];

  const handleNext = async (stepData: any) => {
    const newData = { ...onboardingData, ...stepData };
    setOnboardingData(newData);

    if (currentStep === steps.length - 1) {
      // Complete onboarding
      await completeOnboarding(newData);
    } else {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const completeOnboarding = async (data: OnboardingData) => {
    try {
      // Save onboarding data to backend
      await fetch('/api/v1/users/onboarding', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      // Redirect to dashboard
      router.push('/dashboard');
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
    }
  };

  const CurrentStepComponent = steps[currentStep].component;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex justify-between mb-2">
            {steps.map((step, idx) => (
              <div
                key={step.id}
                className={`flex-1 text-center ${
                  idx <= currentStep ? 'text-blue-600' : 'text-gray-400'
                }`}
              >
                <div className="text-xs font-medium mb-1">{step.title}</div>
              </div>
            ))}
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all duration-300"
              style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Current step content */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <CurrentStepComponent
            onNext={handleNext}
            onBack={handleBack}
            data={onboardingData}
          />
        </div>
      </div>
    </div>
  );
}
