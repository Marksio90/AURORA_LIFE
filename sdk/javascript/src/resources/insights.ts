import { AxiosInstance } from 'axios';
import { Insight, GenerateInsightInput, PaginatedResponse, ListParams } from '../types';

export class InsightsResource {
  constructor(private client: AxiosInstance) {}

  /**
   * List insights with pagination
   */
  async list(params?: ListParams): Promise<PaginatedResponse<Insight>> {
    const response = await this.client.get<PaginatedResponse<Insight>>('/api/v1/insights', { params });
    return response.data;
  }

  /**
   * Get a specific insight
   */
  async get(insightId: string): Promise<Insight> {
    const response = await this.client.get<Insight>(`/api/v1/insights/${insightId}`);
    return response.data;
  }

  /**
   * Generate new AI insights
   */
  async generate(data?: GenerateInsightInput): Promise<Insight[]> {
    const response = await this.client.post<Insight[]>('/api/v1/insights/generate', data || {});
    return response.data;
  }

  /**
   * Mark insight as read
   */
  async markAsRead(insightId: string): Promise<Insight> {
    const response = await this.client.patch<Insight>(`/api/v1/insights/${insightId}/read`);
    return response.data;
  }

  /**
   * Delete an insight
   */
  async delete(insightId: string): Promise<void> {
    await this.client.delete(`/api/v1/insights/${insightId}`);
  }
}
