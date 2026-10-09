import React, { useState, useRef, useEffect, useImperativeHandle, forwardRef } from 'react';
import { ArrowUp, Database } from 'lucide-react';

export interface MessageComposerHandle {
  focusWithText: (text: string) => void;
}

interface MessageComposerProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export const MessageComposer = forwardRef<MessageComposerHandle, MessageComposerProps>(
  ({ onSendMessage, isLoading }, ref) => {
    const [input, setInput] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const trimmed = input.trim();
    const canSubmit = trimmed.length > 0 && !isLoading && trimmed.length <= 2000;

    useImperativeHandle(ref, () => ({
      focusWithText: (text: string) => {
        setInput(text);
        if (textareaRef.current) {
          textareaRef.current.focus();
          // Move cursor to end
          textareaRef.current.setSelectionRange(text.length, text.length);
        }
      },
    }));

    useEffect(() => {
      if (!isLoading && textareaRef.current) {
        textareaRef.current.focus();
      }
    }, [isLoading]);

    const handleSubmit = (e?: React.FormEvent) => {
      if (e) e.preventDefault();
      if (!canSubmit) return;
      onSendMessage(trimmed);
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    };

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setInput(e.target.value);
      e.target.style.height = 'auto';
      e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
    };

    return (
      <div className="p-3 sm:p-4 border-t border-[#493653]/40 bg-[#17121F]/80 backdrop-blur-md">
        {/* Top bar with Order data indicator */}
        <div className="flex items-center justify-between px-2 pb-2">
          <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-[#21172D] border border-[#493653]/60 text-[11px] text-[#B8ACBF] select-none">
            <Database className="w-3 h-3 text-[#D19AFF]" />
            <span>Order data (read-only)</span>
          </div>
          {input.length > 1500 && (
            <span
              className={`text-[11px] font-medium tabular-nums ${
                input.length > 1950 ? 'text-[#FF777F]' : 'text-[#F2C66D]'
              }`}
            >
              {input.length} / 2000
            </span>
          )}
        </div>

        {/* Composer Input Surface */}
        <form
          onSubmit={handleSubmit}
          className="relative flex items-end gap-2.5 p-2 sm:p-3 rounded-[20px] bg-[#2B2037]/75 border border-[#D19AFF]/25 focus-within:border-[#D19AFF]/80 focus-within:ring-2 focus-within:ring-[#B45BFF]/30 transition-all shadow-inner"
        >
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            rows={1}
            placeholder="Ask anything about your orders..."
            maxLength={2000}
            className="flex-1 max-h-40 bg-transparent text-sm text-[#F6F0FA] placeholder-[#8D8197] resize-none focus:outline-none py-1.5 px-2 leading-relaxed"
            aria-label="Ask anything about your orders"
          />

          {/* Circular Purple Send Button (42px) with white up-arrow */}
          <div className="pb-0.5 pr-0.5 shrink-0">
            <button
              type="submit"
              disabled={!canSubmit}
              aria-label="Send message"
              className={`w-[42px] h-[42px] rounded-full flex items-center justify-center transition-all duration-150 ${
                canSubmit
                  ? 'bg-[#B45BFF] hover:bg-[#D19AFF] text-white shadow-lg shadow-[#B45BFF]/35 cursor-pointer hover:scale-105 active:scale-95'
                  : 'bg-[#493653]/40 text-[#8D8197] cursor-not-allowed opacity-60'
              } focus:outline-none focus:ring-2 focus:ring-[#B45BFF] focus:ring-offset-2 focus:ring-offset-[#17121F]`}
            >
              <ArrowUp className="w-5 h-5 stroke-[2.5]" />
            </button>
          </div>
        </form>

        {/* Helper footer text */}
        <p className="text-[11px] text-[#8D8197] text-center pt-2 select-none">
          Answers are based on the supplied order dataset.
        </p>
      </div>
    );
  }
);

MessageComposer.displayName = 'MessageComposer';
