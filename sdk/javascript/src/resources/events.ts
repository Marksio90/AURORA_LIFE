import { AxiosInstance } from 'axios';
import { Event, CreateEventInput, UpdateEventInput, EventListParams, PaginatedResponse } from '../types';

export class EventsResource {
  constructor(private client: AxiosInstance) {}

  /**
   * List events with pagination and filtering
   */
  async list(params?: EventListParams): Promise<PaginatedResponse<Event>> {
    const response = await this.client.get<PaginatedResponse<Event>>('/api/v1/events', { params });
    return response.data;
  }

  /**
   * Get a specific event by ID
   */
  async get(eventId: string): Promise<Event> {
    const response = await this.client.get<Event>(`/api/v1/events/${eventId}`);
    return response.data;
  }

  /**
   * Create a new event
   */
  async create(data: CreateEventInput): Promise<Event> {
    const response = await this.client.post<Event>('/api/v1/events', data);
    return response.data;
  }

  /**
   * Update an existing event
   */
  async update(eventId: string, data: UpdateEventInput): Promise<Event> {
    const response = await this.client.put<Event>(`/api/v1/events/${eventId}`, data);
    return response.data;
  }

  /**
   * Delete an event
   */
  async delete(eventId: string): Promise<void> {
    await this.client.delete(`/api/v1/events/${eventId}`);
  }

  /**
   * Batch create events
   */
  async batchCreate(events: CreateEventInput[]): Promise<Event[]> {
    const response = await this.client.post<Event[]>('/api/v1/events/batch', { events });
    return response.data;
  }
}
