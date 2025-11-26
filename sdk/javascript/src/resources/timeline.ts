import { AxiosInstance } from 'axios';
import { TimelineData } from '../types';

export class TimelineResource {
  constructor(private client: AxiosInstance) {}

  /**
   * Get timeline data for a date range
   */
  async get(days: number = 30): Promise<TimelineData[]> {
    const response = await this.client.get<TimelineData[]>('/api/v1/timeline', {
      params: { days },
    });
    return response.data;
  }

  /**
   * Get timeline aggregations
   */
  async aggregations(startDate?: string, endDate?: string): Promise<Record<string, any>> {
    const response = await this.client.get<Record<string, any>>('/api/v1/timeline/aggregations', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  }
}
