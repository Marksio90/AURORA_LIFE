/**
 * AURORA_LIFE API Client
 * Axios-based client with auth interceptors and type-safe endpoints
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  User,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  LifeEvent,
  LifeEventCreate,
  LifeEventUpdate,
  TimelineResponse,
  EnergyPrediction,
  MoodPrediction,
  DataGeniusAnalysis,
  AgentAnalysis,
  AIInsight,
  PaginatedResponse,
  PaginationParams,
  WhatIfScenario,
  WhatIfResult,
  VaultItem,
  VaultItemCreate,
} from '@/types/api';

// ============================================================================
// API Configuration
// ============================================================================

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30 seconds
    });

    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Unauthorized - clear token and redirect to login
          this.clearToken();
          if (typeof window !== 'undefined') {
            window.location.href = '/auth/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // ============================================================================
  // Token Management
  // ============================================================================

  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('aurora_access_token');
  }

  private setToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem('aurora_access_token', token);
  }

  private clearToken(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('aurora_access_token');
    localStorage.removeItem('aurora_user');
  }

  // ============================================================================
  // Authentication Endpoints
  // ============================================================================

  auth = {
    login: async (credentials: LoginRequest): Promise<AuthResponse> => {
      // OAuth2 password flow requires form data
      const formData = new URLSearchParams();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);

      const { data } = await this.client.post<AuthResponse>(
        '/api/auth/login',
        formData,
        {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        }
      );

      this.setToken(data.access_token);
      localStorage.setItem('aurora_user', JSON.stringify(data.user));
      return data;
    },

    register: async (userData: RegisterRequest): Promise<AuthResponse> => {
      const { data } = await this.client.post<AuthResponse>(
        '/api/auth/register',
        userData
      );

      this.setToken(data.access_token);
      localStorage.setItem('aurora_user', JSON.stringify(data.user));
      return data;
    },

    logout: async (): Promise<void> => {
      this.clearToken();
    },

    getCurrentUser: async (): Promise<User> => {
      const { data } = await this.client.get<User>('/api/auth/me');
      return data;
    },

    // OAuth providers
    googleLogin: (redirectUrl?: string): void => {
      const url = redirectUrl
        ? `${API_BASE_URL}/api/auth/oauth/google?redirect_url=${encodeURIComponent(redirectUrl)}`
        : `${API_BASE_URL}/api/auth/oauth/google`;
      window.location.href = url;
    },

    githubLogin: (redirectUrl?: string): void => {
      const url = redirectUrl
        ? `${API_BASE_URL}/api/auth/oauth/github?redirect_url=${encodeURIComponent(redirectUrl)}`
        : `${API_BASE_URL}/api/auth/oauth/github`;
      window.location.href = url;
    },
  };

  // ============================================================================
  // User Endpoints
  // ============================================================================

  users = {
    getMe: async (): Promise<User> => {
      const { data } = await this.client.get<User>('/api/users/me');
      return data;
    },

    updateMe: async (updates: Partial<User>): Promise<User> => {
      const { data } = await this.client.put<User>('/api/users/me', updates);
      return data;
    },

    getDigitalTwin: async (userId: number): Promise<any> => {
      const { data } = await this.client.get(`/api/users/${userId}/digital-twin`);
      return data;
    },
  };

  // ============================================================================
  // Life Events Endpoints
  // ============================================================================

  events = {
    list: async (
      params?: PaginationParams & {
        event_type?: string;
        start_time?: string;
        end_time?: string;
      }
    ): Promise<PaginatedResponse<LifeEvent>> => {
      const { data } = await this.client.get<PaginatedResponse<LifeEvent>>(
        '/api/events/',
        { params }
      );
      return data;
    },

    get: async (eventId: number): Promise<LifeEvent> => {
      const { data } = await this.client.get<LifeEvent>(`/api/events/${eventId}`);
      return data;
    },

    create: async (event: LifeEventCreate): Promise<LifeEvent> => {
      const { data } = await this.client.post<LifeEvent>('/api/events/', event);
      return data;
    },

    update: async (
      eventId: number,
      updates: LifeEventUpdate
    ): Promise<LifeEvent> => {
      const { data } = await this.client.put<LifeEvent>(
        `/api/events/${eventId}`,
        updates
      );
      return data;
    },

    delete: async (eventId: number): Promise<void> => {
      await this.client.delete(`/api/events/${eventId}`);
    },
  };

  // ============================================================================
  // Timeline Endpoints
  // ============================================================================

  timeline = {
    get: async (days: number = 7): Promise<TimelineResponse> => {
      const { data } = await this.client.get<TimelineResponse>(
        `/api/timeline/${days}d`
      );
      return data;
    },
  };

  // ============================================================================
  // AI/ML Prediction Endpoints
  // ============================================================================

  predictions = {
    energy: async (
      timeOfDay: 'morning' | 'afternoon' | 'evening' = 'morning'
    ): Promise<EnergyPrediction> => {
      const { data } = await this.client.post<EnergyPrediction>(
        '/api/ai/predict/energy',
        { time_of_day: timeOfDay }
      );
      return data;
    },

    mood: async (context?: Record<string, any>): Promise<MoodPrediction> => {
      const { data } = await this.client.post<MoodPrediction>(
        '/api/ai/predict/mood',
        { context }
      );
      return data;
    },
  };

  // ============================================================================
  // DataGenius Analysis Endpoints
  // ============================================================================

  analysis = {
    patterns: async (days: number = 30): Promise<DataGeniusAnalysis> => {
      const { data } = await this.client.get<DataGeniusAnalysis>(
        '/api/ai/analyze/',
        { params: { days } }
      );
      return data;
    },

    whatIf: async (scenario: WhatIfScenario): Promise<WhatIfResult> => {
      const { data } = await this.client.post<WhatIfResult>(
        '/api/ai/whatif/simulate',
        scenario
      );
      return data;
    },
  };

  // ============================================================================
  // AI Agents Endpoints
  // ============================================================================

  agents = {
    runAll: async (): Promise<AgentAnalysis[]> => {
      const { data } = await this.client.post<AgentAnalysis[]>(
        '/api/ai/agents/run-all/'
      );
      return data;
    },

    runAgent: async (
      agentName: string,
      context?: Record<string, any>
    ): Promise<AgentAnalysis> => {
      const { data } = await this.client.post<AgentAnalysis>(
        `/api/ai/agents/${agentName}`,
        { context }
      );
      return data;
    },
  };

  // ============================================================================
  // Insights Endpoints
  // ============================================================================

  insights = {
    list: async (
      params?: PaginationParams
    ): Promise<PaginatedResponse<AIInsight>> => {
      const { data } = await this.client.get<PaginatedResponse<AIInsight>>(
        '/api/insights/',
        { params }
      );
      return data;
    },

    get: async (insightId: number): Promise<AIInsight> => {
      const { data } = await this.client.get<AIInsight>(
        `/api/insights/${insightId}`
      );
      return data;
    },
  };

  // ============================================================================
  // Vault (Secure Storage) Endpoints
  // ============================================================================

  vault = {
    list: async (category?: string): Promise<VaultItem[]> => {
      const { data} = await this.client.get<VaultItem[]>('/api/vault/', {
        params: { category },
      });
      return data;
    },

    get: async (key: string): Promise<{ value: string }> => {
      const { data } = await this.client.get<{ value: string }>(
        `/api/vault/${key}`
      );
      return data;
    },

    set: async (item: VaultItemCreate): Promise<VaultItem> => {
      const { data } = await this.client.post<VaultItem>('/api/vault/', item);
      return data;
    },

    delete: async (key: string): Promise<void> => {
      await this.client.delete(`/api/vault/${key}`);
    },
  };

  // ============================================================================
  // Health Check
  // ============================================================================

  health = {
    check: async (): Promise<{ status: string }> => {
      const { data } = await this.client.get<{ status: string }>('/health');
      return data;
    },
  };
}

// Export singleton instance
export const api = new APIClient();
