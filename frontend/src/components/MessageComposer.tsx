import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';

interface MessageComposerProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export const MessageComposer: React.FC<MessageComposerProps> = ({
  onSendMessage,
  isLoading,
}) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const trimmed = input.trim();
  const canSubmit = trimmed.length > 0 && !isLoading && trimmed.length <= 2000;

  useEffect(() => {
    if (!isLoading && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
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
      handleSubmit(e);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto resize
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-3 sm:p-4 border-t border-[#493653]/40 bg-[#17121F]/80 backdrop-blur-md"
      aria-label="Send a message to Milo"
    >
      <div className="relative flex items-end gap-2 p-2 sm:p-2.5 rounded-2xl bg-[#2B2037]/70 border border-[#493653]/60 focus-within:border-[#B45BFF]/70 focus-within:ring-2 focus-within:ring-[#B45BFF]/30 transition-all shadow-inner">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={1}
          placeholder="Ask a question about orders, revenue, or customers..."
          maxLength={2000}
          className="flex-1 max-h-40 bg-transparent text-sm text-[#F6F0FA] placeholder-[#8D8197] resize-none focus:outline-none py-1.5 px-2 leading-relaxed"
          aria-label="Message input"
        />

        <div className="flex items-center gap-2 pb-0.5 pr-0.5 shrink-0">
          <button
            type="submit"
            disabled={!canSubmit}
            aria-label="Send message"
            className={`p-2.5 rounded-xl flex items-center justify-center transition-all ${
              canSubmit
                ? 'bg-[#B45BFF] hover:bg-[#D19AFF] text-white shadow-md shadow-[#B45BFF]/25 cursor-pointer hover:scale-105 active:scale-95'
                : 'bg-[#493653]/40 text-[#8D8197] cursor-not-allowed'
            } focus:outline-none focus:ring-2 focus:ring-[#B45BFF]`}
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex items-center justify-between text-[11px] text-[#8D8197] px-2 pt-2">
        <span className="hidden sm:inline-flex items-center gap-1">
          <kbd className="px-1.5 py-0.5 rounded bg-[#2B2037] border border-[#493653]/60 text-[10px]">Enter</kbd> to send,
          <kbd className="px-1.5 py-0.5 rounded bg-[#2B2037] border border-[#493653]/60 text-[10px]">Shift+Enter</kbd> for newline
        </span>
        <span className={`${input.length > 1800 ? 'text-[#FF777F]' : ''} ml-auto`}>
          {input.length} / 2000
        </span>
      </div>
    </form>
  );
};
