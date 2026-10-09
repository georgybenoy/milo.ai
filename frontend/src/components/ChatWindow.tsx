import React, { useRef, useEffect } from 'react';
import { WelcomeScreen } from './WelcomeScreen';
import { MessageBubble } from './MessageBubble';
import { LoadingIndicator } from './LoadingIndicator';
import { ErrorMessage } from './ErrorMessage';
import type { ChatMessage } from '../types';

interface ChatWindowProps {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  onSelectQuery: (query: string) => void;
  onFocusComposer?: (prefill?: string) => void;
  onRetry?: () => void;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  isLoading,
  error,
  onSelectQuery,
  onFocusComposer,
  onRetry,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollEndRef = useRef<HTMLDivElement>(null);
  const isNearBottomRef = useRef(true);

  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    // User is near bottom if within 120px of end
    isNearBottomRef.current = scrollHeight - scrollTop - clientHeight < 120;
  };

  useEffect(() => {
    if (isNearBottomRef.current) {
      scrollEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading, error]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 overflow-y-auto px-4 py-6 scroll-smooth">
        <WelcomeScreen
          onSelectQuery={onSelectQuery}
          onFocusComposer={onFocusComposer}
        />
        {error && (
          <div className="max-w-3xl mx-auto mt-4">
            <ErrorMessage message={error} onRetry={onRetry} />
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      role="log"
      aria-live="polite"
      className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 scroll-smooth"
    >
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {isLoading && (
        <div className="flex justify-start">
          <LoadingIndicator />
        </div>
      )}

      {error && (
        <div className="flex justify-start">
          <ErrorMessage message={error} onRetry={onRetry} />
        </div>
      )}

      <div ref={scrollEndRef} aria-hidden="true" className="h-2" />
    </div>
  );
};
