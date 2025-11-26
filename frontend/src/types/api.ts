/**
 * TypeScript type definitions for AURORA_LIFE API
 */

// ============================================================================
// User & Auth Types
// ============================================================================

export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  timezone?: string;
  is_active: boolean;
  is_verified: boolean;
  role: 'user' | 'admin' | 'moderator';
  health_score?: number;
  energy_score?: number;
  mood_score?: number;
  productivity_score?: number;
  profile_data?: Record<string, any>;
  created_at: string;
  updated_at?: string;
  last_active?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  full_name?: string;
  timezone?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface OAuthAccount {
  id: number;
  user_id: number;
  provider: 'google' | 'github';
  provider_user_id: string;
  created_at: string;
}

// ============================================================================
// Life Event Types
// ============================================================================

export type EventType =
  | 'sleep'
  | 'exercise'
  | 'activity'
  | 'emotion'
  | 'work'
  | 'social'
  | 'health'
  | 'meal'
  | 'travel'
  | 'learning'
  | 'entertainment';

export type EventCategory =
  | 'physical'
  | 'mental'
  | 'social'
  | 'professional'
  | 'personal';

export interface LifeEvent {
  id: number;
  user_id: number;
  event_type: EventType;
  event_category: EventCategory;
  title: string;
  description?: string;
  event_data?: Record<string, any>;
  event_time: string;
  duration_minutes?: number;
  end_time?: string;
  impact_score?: number;
  energy_impact?: number;
  mood_impact?: number;
  tags?: string[];
  context?: Record<string, any>;
  source?: string;
  created_at: string;
  updated_at?: string;
}

export interface LifeEventCreate {
  event_type: EventType;
  event_category: EventCategory;
  title: string;
  description?: string;
  event_data?: Record<string, any>;
  event_time: string;
  duration_minutes?: number;
  tags?: string[];
  context?: Record<string, any>;
  source?: string;
}

export interface LifeEventUpdate {
  title?: string;
  description?: string;
  event_data?: Record<string, any>;
  tags?: string[];
  context?: Record<string, any>;
}

// ============================================================================
// Timeline Types
// ============================================================================

export interface TimelineEntry {
  id: number;
  event_time: string;
  title: string;
  event_type: EventType;
  event_category: EventCategory;
  impact_score?: number;
  energy_impact?: number;
  mood_impact?: number;
}

export interface TimelineResponse {
  user_id: number;
  period_days: number;
  total_events: number;
  entries: TimelineEntry[];
  patterns?: Record<string, any>;
}

// ============================================================================
// Prediction Types
// ============================================================================

export interface EnergyPrediction {
  user_id: number;
  time_of_day: 'morning' | 'afternoon' | 'evening';
  predicted_energy: number;
  confidence: number;
  factors: string[];
  recommendations: string[];
}

export interface MoodPrediction {
  user_id: number;
  predicted_mood_score: number;
  prediction_class: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  confidence: number;
  class_probabilities?: Record<string, number>;
  influencing_factors: string[];
}

// ============================================================================
// AI Analysis Types
// ============================================================================

export interface AIInsight {
  id: number;
  user_id: number;
  insight_type: string;
  title: string;
  content: string;
  priority: 'low' | 'medium' | 'high';
  category: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface AgentAnalysis {
  agent: string;
  analysis: Record<string, any>;
  recommendations: Record<string, any>;
  timestamp: string;
}

export interface DataGeniusAnalysis {
  user_id: number;
  period_days: number;
  events_analyzed: number;
  features: Record<string, any>;
  insights: any[];
  scores: {
    overall_wellbeing?: number;
    sleep_quality?: number;
    physical_activity?: number;
    social_engagement?: number;
    productivity?: number;
  };
  analyzed_at: string;
}

// ============================================================================
// Pagination Types
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
}

// ============================================================================
// API Error Types
// ============================================================================

export interface APIError {
  detail: string;
  status_code?: number;
}

export interface ValidationError {
  loc: string[];
  msg: string;
  type: string;
}

// ============================================================================
// WhatIf Analysis Types
// ============================================================================

export interface WhatIfScenario {
  scenario_name: string;
  changes: Record<string, any>;
  duration_days?: number;
}

export interface WhatIfResult {
  scenario_name: string;
  baseline: Record<string, any>;
  predicted: Record<string, any>;
  delta: Record<string, any>;
  confidence: number;
  recommendations: string[];
}

// ============================================================================
// Vault (Secure Storage) Types
// ============================================================================

export interface VaultItem {
  id: number;
  user_id: number;
  key: string;
  encrypted_value: string;
  category?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface VaultItemCreate {
  key: string;
  value: string;
  category?: string;
  metadata?: Record<string, any>;
}

// ============================================================================
// Notification Types
// ============================================================================

export interface Notification {
  id: number;
  user_id: number;
  type: string;
  title: string;
  content: string;
  is_read: boolean;
  priority: 'low' | 'medium' | 'high';
  created_at: string;
}

// ============================================================================
// Chart Data Types
// ============================================================================

export interface ChartDataPoint {
  date: string;
  value: number;
  label?: string;
}

export interface EnergyChartData {
  morning: ChartDataPoint[];
  afternoon: ChartDataPoint[];
  evening: ChartDataPoint[];
}

export interface MoodChartData {
  dates: string[];
  scores: number[];
  sentiments: ('positive' | 'negative' | 'neutral')[];
}
