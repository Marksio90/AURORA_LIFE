# AURORA_LIFE JavaScript/TypeScript SDK

Official JavaScript/TypeScript SDK for the AURORA_LIFE API.

## Installation

```bash
npm install @auroralife/sdk
# or
yarn add @auroralife/sdk
# or
pnpm add @auroralife/sdk
```

## Quick Start

```typescript
import { AuroraLifeClient } from '@auroralife/sdk';

// Initialize client
const client = new AuroraLifeClient({
  apiKey: 'your-api-key',
  baseURL: 'https://api.auroralife.example.com' // optional
});

// Create an event
const event = await client.events.create({
  eventType: 'sleep',
  title: 'Good night sleep',
  eventTime: new Date().toISOString(),
  eventData: {
    duration_hours: 8,
    quality: 'excellent'
  }
});

// Get predictions
const energy = await client.predictions.energy();
console.log(`Predicted energy: ${energy.prediction}/10`);

const mood = await client.predictions.mood();
console.log(`Predicted mood: ${mood.prediction_class}`);

// Generate AI insights
const insights = await client.insights.generate({
  context: 'health',
  time_range_days: 7
});
```

## Features

- ✅ Full TypeScript support with type definitions
- ✅ Promise-based async/await API
- ✅ Automatic retries on network failures
- ✅ Comprehensive error handling
- ✅ Request/response interceptors
- ✅ Pagination support
- ✅ Batch operations
- ✅ Node.js and browser compatible

## API Reference

### Client Configuration

```typescript
const client = new AuroraLifeClient({
  apiKey: string;        // Required: Your API key or JWT token
  baseURL?: string;      // Optional: API base URL (default: https://api.auroralife.example.com)
  timeout?: number;      // Optional: Request timeout in ms (default: 30000)
  maxRetries?: number;   // Optional: Max retry attempts (default: 3)
  headers?: object;      // Optional: Custom headers
});
```

### Events

```typescript
// List events
const events = await client.events.list({
  page: 1,
  page_size: 20,
  event_type: 'sleep',
  start_date: '2024-01-01',
  end_date: '2024-01-31'
});

// Get single event
const event = await client.events.get('event-id');

// Create event
const newEvent = await client.events.create({
  event_type: 'exercise',
  title: 'Morning run',
  event_time: '2024-01-16T07:00:00Z',
  event_data: {
    duration_minutes: 30,
    distance_km: 5.2
  },
  tags: ['cardio', 'outdoor']
});

// Update event
const updated = await client.events.update('event-id', {
  title: 'Updated title',
  event_data: { duration_minutes: 45 }
});

// Delete event
await client.events.delete('event-id');

// Batch create
const batchEvents = await client.events.batchCreate([
  { event_type: 'sleep', title: 'Night sleep', event_time: '2024-01-15T23:00:00Z' },
  { event_type: 'mood', title: 'Morning mood', event_time: '2024-01-16T08:00:00Z' }
]);
```

### Predictions

```typescript
// Get energy prediction
const energyPrediction = await client.predictions.energy();
// { prediction: 7.8, confidence: 0.85, ... }

// Get mood prediction
const moodPrediction = await client.predictions.mood();
// { prediction_class: 'positive', confidence: 0.72, ... }

// Get historical predictions
const history = await client.predictions.list('energy', 10);
```

### Insights

```typescript
// List insights
const insights = await client.insights.list({
  page: 1,
  page_size: 10
});

// Get single insight
const insight = await client.insights.get('insight-id');

// Generate new insights
const newInsights = await client.insights.generate({
  context: 'productivity',
  time_range_days: 14,
  focus_areas: ['work', 'energy']
});

// Mark as read
await client.insights.markAsRead('insight-id');

// Delete insight
await client.insights.delete('insight-id');
```

### Users

```typescript
// Get current user
const user = await client.users.me();

// Update profile
const updated = await client.users.update({
  full_name: 'John Doe',
  preferences: {
    theme: 'dark',
    notifications_enabled: true
  }
});

// Delete account
await client.users.deleteAccount();
```

### Timeline

```typescript
// Get timeline (last 30 days by default)
const timeline = await client.timeline.get(30);

// Get aggregations
const aggregations = await client.timeline.aggregations(
  '2024-01-01',
  '2024-01-31'
);
```

## Error Handling

The SDK provides specific error types for different scenarios:

```typescript
import {
  AuroraLifeError,
  AuthenticationError,
  ValidationError,
  RateLimitError
} from '@auroralife/sdk';

try {
  await client.events.create({ /* ... */ });
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error('Invalid API key');
  } else if (error instanceof ValidationError) {
    console.error('Validation failed:', error.details);
  } else if (error instanceof RateLimitError) {
    console.error('Rate limit exceeded');
  } else if (error instanceof AuroraLifeError) {
    console.error('API error:', error.message);
  }
}
```

## Advanced Usage

### Custom Requests

```typescript
// Make a custom API request
const response = await client.request({
  method: 'POST',
  url: '/api/v1/custom-endpoint',
  data: { key: 'value' }
});
```

### Update API Key

```typescript
// Update the API key at runtime
client.setApiKey('new-api-key');
```

## TypeScript Support

The SDK is written in TypeScript and provides full type definitions:

```typescript
import type { Event, CreateEventInput, Prediction } from '@auroralife/sdk';

const eventData: CreateEventInput = {
  event_type: 'sleep',
  title: 'Sleep',
  event_time: new Date().toISOString()
};

const event: Event = await client.events.create(eventData);
const prediction: Prediction = await client.predictions.energy();
```

## Examples

### Track Daily Routine

```typescript
const client = new AuroraLifeClient({ apiKey: 'your-key' });

// Morning routine
await client.events.create({
  event_type: 'sleep',
  title: 'Night sleep',
  event_time: new Date('2024-01-16T07:00:00Z').toISOString(),
  event_data: { duration_hours: 7.5, quality: 'good' }
});

await client.events.create({
  event_type: 'exercise',
  title: 'Morning workout',
  event_time: new Date('2024-01-16T07:30:00Z').toISOString(),
  event_data: { duration_minutes: 30, type: 'strength_training' }
});

// Get predictions for the day
const energy = await client.predictions.energy();
const mood = await client.predictions.mood();

console.log(`Today's predictions:`);
console.log(`- Energy: ${energy.prediction}/10`);
console.log(`- Mood: ${mood.prediction_class}`);
```

### Weekly Analysis

```typescript
// Get all events from last week
const weekAgo = new Date();
weekAgo.setDate(weekAgo.getDate() - 7);

const events = await client.events.list({
  start_date: weekAgo.toISOString(),
  end_date: new Date().toISOString(),
  page_size: 100
});

// Generate insights
const insights = await client.insights.generate({
  context: 'wellbeing',
  time_range_days: 7
});

console.log('Weekly insights:');
insights.forEach(insight => {
  console.log(`- ${insight.title}: ${insight.content}`);
});
```

## Contributing

See the [contributing guide](../../CONTRIBUTING.md) for development setup and guidelines.

## License

MIT
