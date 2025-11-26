/**
 * Common types used across the SDK
 */

export interface Event {
  id: string;
  user_id: string;
  event_type: string;
  title: string;
  description?: string;
  event_time: string;
  event_data: Record<string, any>;
  tags?: string[];
  created_at: string;
  updated_at: string;
}

export interface CreateEventInput {
  event_type: string;
  title: string;
  description?: string;
  event_time: string;
  event_data?: Record<string, any>;
  tags?: string[];
}

export interface UpdateEventInput {
  title?: string;
  description?: string;
  event_time?: string;
  event_data?: Record<string, any>;
  tags?: string[];
}

export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  is_verified: boolean;
  role: string;
  preferences?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface UpdateUserInput {
  full_name?: string;
  preferences?: Record<string, any>;
}

export interface Prediction {
  id: string;
  user_id: string;
  model_type: 'energy' | 'mood';
  prediction?: number;
  prediction_class?: string;
  confidence?: number;
  class_probabilities?: Record<string, number>;
  features_used?: Record<string, any>;
  model_version?: string;
  created_at: string;
}

export interface Insight {
  id: string;
  user_id: string;
  title: string;
  content: string;
  insight_type?: string;
  context?: string;
  confidence?: number;
  metadata?: Record<string, any>;
  is_read: boolean;
  created_at: string;
}

export interface GenerateInsightInput {
  context?: string;
  time_range_days?: number;
  focus_areas?: string[];
}

export interface TimelineData {
  date: string;
  events: Event[];
  event_counts: Record<string, number>;
  metrics?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface ListParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface EventListParams extends ListParams {
  event_type?: string;
  start_date?: string;
  end_date?: string;
  tags?: string[];
}
