export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolUsed?: string;
  timestamp: Date;
}

export interface ChatResponse {
  reply: string;
  tool_used: string | null;
}

export interface HealthResponse {
  status: string;
  orders_loaded: number;
  model: string;
}

export interface SuggestedQuestion {
  text: string;
  icon: string;
}
