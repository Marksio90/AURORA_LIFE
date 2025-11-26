/**
 * AURORA_LIFE JavaScript/TypeScript SDK
 *
 * Official SDK for interacting with the AURORA_LIFE API.
 *
 * @example
 * ```typescript
 * import { AuroraLifeClient } from '@auroralife/sdk';
 *
 * const client = new AuroraLifeClient({
 *   apiKey: 'your-api-key',
 *   baseURL: 'https://api.auroralife.example.com'
 * });
 *
 * // Create an event
 * const event = await client.events.create({
 *   eventType: 'sleep',
 *   title: 'Good night sleep',
 *   eventTime: new Date().toISOString(),
 *   eventData: { duration_hours: 8, quality: 'excellent' }
 * });
 *
 * // Get predictions
 * const energy = await client.predictions.energy();
 * const mood = await client.predictions.mood();
 * ```
 */

export { AuroraLifeClient } from './client';
export * from './types';
export * from './errors';
export * from './resources';
