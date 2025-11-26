import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { EventsResource } from './resources/events';
import { UsersResource } from './resources/users';
import { PredictionsResource } from './resources/predictions';
import { InsightsResource } from './resources/insights';
import { TimelineResource } from './resources/timeline';
import { AuroraLifeError, AuthenticationError, ValidationError, RateLimitError } from './errors';

export interface AuroraLifeClientConfig {
  /** API key or JWT token for authentication */
  apiKey: string;

  /** Base URL for the API (default: https://api.auroralife.example.com) */
  baseURL?: string;

  /** Request timeout in milliseconds (default: 30000) */
  timeout?: number;

  /** Maximum number of retries for failed requests (default: 3) */
  maxRetries?: number;

  /** Custom headers to include with all requests */
  headers?: Record<string, string>;
}

export class AuroraLifeClient {
  private httpClient: AxiosInstance;
  private config: Required<AuroraLifeClientConfig>;

  // Resource clients
  public events: EventsResource;
  public users: UsersResource;
  public predictions: PredictionsResource;
  public insights: InsightsResource;
  public timeline: TimelineResource;

  constructor(config: AuroraLifeClientConfig) {
    // Set defaults
    this.config = {
      apiKey: config.apiKey,
      baseURL: config.baseURL || 'https://api.auroralife.example.com',
      timeout: config.timeout || 30000,
      maxRetries: config.maxRetries || 3,
      headers: config.headers || {},
    };

    // Create HTTP client
    this.httpClient = axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      headers: {
        'Authorization': `Bearer ${this.config.apiKey}`,
        'Content-Type': 'application/json',
        'User-Agent': '@auroralife/sdk-js/0.1.0',
        ...this.config.headers,
      },
    });

    // Add response interceptor for error handling
    this.httpClient.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response) {
          const { status, data } = error.response;

          // Handle specific error types
          if (status === 401) {
            throw new AuthenticationError(data.detail || 'Authentication failed');
          } else if (status === 422) {
            throw new ValidationError(data.detail || 'Validation error', data);
          } else if (status === 429) {
            throw new RateLimitError(data.detail || 'Rate limit exceeded');
          } else {
            throw new AuroraLifeError(
              data.detail || `Request failed with status ${status}`,
              status
            );
          }
        } else if (error.request) {
          // Network error
          throw new AuroraLifeError('Network error: No response received');
        } else {
          throw new AuroraLifeError(error.message);
        }
      }
    );

    // Initialize resource clients
    this.events = new EventsResource(this.httpClient);
    this.users = new UsersResource(this.httpClient);
    this.predictions = new PredictionsResource(this.httpClient);
    this.insights = new InsightsResource(this.httpClient);
    this.timeline = new TimelineResource(this.httpClient);
  }

  /**
   * Make a custom request to the API
   */
  async request<T = any>(config: AxiosRequestConfig): Promise<T> {
    const response = await this.httpClient.request<T>(config);
    return response.data;
  }

  /**
   * Update the API key
   */
  setApiKey(apiKey: string): void {
    this.config.apiKey = apiKey;
    this.httpClient.defaults.headers.common['Authorization'] = `Bearer ${apiKey}`;
  }

  /**
   * Get the current configuration
   */
  getConfig(): Readonly<AuroraLifeClientConfig> {
    return { ...this.config };
  }
}
