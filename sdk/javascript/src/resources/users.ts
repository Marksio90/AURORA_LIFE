import { AxiosInstance } from 'axios';
import { User, UpdateUserInput } from '../types';

export class UsersResource {
  constructor(private client: AxiosInstance) {}

  /**
   * Get current user profile
   */
  async me(): Promise<User> {
    const response = await this.client.get<User>('/api/v1/users/me');
    return response.data;
  }

  /**
   * Update current user profile
   */
  async update(data: UpdateUserInput): Promise<User> {
    const response = await this.client.put<User>('/api/v1/users/me', data);
    return response.data;
  }

  /**
   * Delete current user account
   */
  async deleteAccount(): Promise<void> {
    await this.client.delete('/api/v1/users/me');
  }
}
