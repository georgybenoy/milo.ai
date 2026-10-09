/**
 * API client for communicating with Milo backend.
 */

import type { ChatResponse, HealthResponse, DatasetInfo } from '../types';

const API_BASE = '/api';

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Health check returned status ${response.status}`);
  }
  return response.json();
}

export async function fetchDatasetInfo(): Promise<DatasetInfo> {
  const response = await fetch(`${API_BASE}/dataset`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Dataset endpoint returned status ${response.status}`);
  }
  return response.json();
}

export async function postChatMessage(message: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ message }),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const errorText = data?.error || `Chat request failed (${response.status})`;
    return {
      reply: null,
      error: errorText,
    };
  }

  return data;
}
