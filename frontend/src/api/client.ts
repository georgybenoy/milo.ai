/**
 * API client for communicating with Milo backend.
 * Implements defensive validation, timeouts, signal abortion, and friendly error mapping.
 */

import type { ChatResponse, HealthResponse, DatasetInfo } from '../types';

const API_BASE = '/api';
const TIMEOUT_MS = 60000; // 60s timeout

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  try {
    const response = await fetch(`${API_BASE}/health`, {
      headers: { 'Accept': 'application/json' },
      signal: signal || controller.signal,
    });
    if (!response.ok) {
      throw new Error(`Health check returned status ${response.status}`);
    }
    return await response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function fetchDatasetInfo(signal?: AbortSignal): Promise<DatasetInfo> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  try {
    const response = await fetch(`${API_BASE}/dataset`, {
      headers: { 'Accept': 'application/json' },
      signal: signal || controller.signal,
    });
    if (!response.ok) {
      throw new Error(`Dataset endpoint returned status ${response.status}`);
    }
    return await response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function postChatMessage(
  message: string,
  externalSignal?: AbortSignal
): Promise<ChatResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  // Combine external abort signal if provided
  const onExternalAbort = () => controller.abort();
  if (externalSignal) {
    if (externalSignal.aborted) {
      controller.abort();
    } else {
      externalSignal.addEventListener('abort', onExternalAbort, { once: true });
    }
  }

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ message }),
      signal: controller.signal,
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      // Status-specific friendly message mapping
      if (response.status === 404) {
        return {
          reply: null,
          error: "I couldn't find that order in the supplied records. Please check the order ID and try again.",
        };
      }
      if (response.status === 502 || response.status === 503) {
        return {
          reply: null,
          error: "Milo is temporarily unavailable. Please try again shortly.",
        };
      }
      if (response.status === 422) {
        return {
          reply: null,
          error: data?.error || "Please enter a valid message (up to 2000 characters).",
        };
      }
      return {
        reply: null,
        error: data?.error || `An error occurred (${response.status}). Please try again shortly.`,
      };
    }

    // Defensive check of returned data shape
    if (typeof data === 'object' && data !== null && 'reply' in data) {
      return {
        reply: typeof data.reply === 'string' ? data.reply : null,
        error: typeof data.error === 'string' ? data.error : null,
      };
    }

    return {
      reply: null,
      error: "Received an unexpected response format from the server.",
    };

  } catch (err: unknown) {
    if (externalSignal?.aborted) {
      // Cancelled by user action (e.g. New Chat)
      return { reply: null, error: null };
    }

    const isAbort = err instanceof DOMException && err.name === 'AbortError';
    if (isAbort) {
      return {
        reply: null,
        error: "Request timed out after 60 seconds. Please try a simpler question.",
      };
    }

    return {
      reply: null,
      error: "I couldn't reach Milo. Check your connection and try again.",
    };
  } finally {
    clearTimeout(timeoutId);
    if (externalSignal) {
      externalSignal.removeEventListener('abort', onExternalAbort);
    }
  }
}
