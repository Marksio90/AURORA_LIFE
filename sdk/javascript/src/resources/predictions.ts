import { AxiosInstance } from 'axios';
import { Prediction } from '../types';

export class PredictionsResource {
  constructor(private client: AxiosInstance) {}

  /**
   * Get energy prediction
   */
  async energy(): Promise<Prediction> {
    const response = await this.client.get<Prediction>('/api/v1/predictions/energy');
    return response.data;
  }

  /**
   * Get mood prediction
   */
  async mood(): Promise<Prediction> {
    const response = await this.client.get<Prediction>('/api/v1/predictions/mood');
    return response.data;
  }

  /**
   * Get historical predictions
   */
  async list(modelType?: 'energy' | 'mood', limit?: number): Promise<Prediction[]> {
    const response = await this.client.get<Prediction[]>('/api/v1/predictions', {
      params: { model_type: modelType, limit },
    });
    return response.data;
  }
}
