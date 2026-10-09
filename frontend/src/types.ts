/**
 * TypeScript types for Milo frontend.
 */

export type Role = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  timestamp: Date;
  toolUsed?: string | null;
  error?: string | null;
}

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  reply: string | null;
  error: string | null;
}

export interface HealthResponse {
  status: string;
  data_loaded: boolean;
  ai_configured: boolean;
}

export type HealthStatus = 'ready' | 'connecting' | 'unavailable';

export interface DatasetInfo {
  record_count: number;
  start_date: string;
  end_date: string;
}

export interface SuggestedQuery {
  id: string;
  title: string;
  query: string;
  category: string;
}

export interface FeatureItem {
  id: string;
  title: string;
  description: string;
  badge?: string;
}

export type LoadingState = 'idle' | 'loading' | 'error' | 'success';
