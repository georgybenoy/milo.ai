import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Wrench, User } from 'lucide-react';
import type { ChatMessage } from '../types';

interface MessageBubbleProps {
  message: ChatMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';

  const formattedTime = new Intl.DateTimeFormat('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(message.timestamp);

  return (
    <div
      className={`flex items-start gap-3 w-full max-w-3xl ${
        isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
      }`}
    >
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 border ${
          isUser
            ? 'bg-[#B45BFF]/20 border-[#B45BFF]/40 text-[#D19AFF]'
            : 'bg-[#2B2037] border-[#493653]/60 text-[#D19AFF] shadow-sm'
        }`}
        aria-hidden="true"
      >
        {isUser ? (
          <User className="w-4 h-4" />
        ) : (
          <img
            src="/milo-logo-transparent.png"
            alt="Milo"
            className="w-4 h-4 object-contain"
          />
        )}
      </div>

      {/* Bubble body */}
      <div className={`space-y-1.5 max-w-[85%] sm:max-w-[75%]`}>
        <div
          className={`p-4 rounded-2xl text-sm leading-relaxed border ${
            isUser
              ? 'bg-[#B45BFF]/20 text-[#F6F0FA] border-[#B45BFF]/35 rounded-tr-sm backdrop-blur-sm'
              : 'bg-[#21172D]/90 text-[#F6F0FA] border-[#493653]/50 rounded-tl-sm shadow-md'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-invert prose-sm max-w-none space-y-2 [&>ul]:list-disc [&>ul]:pl-5 [&>ol]:list-decimal [&>ol]:pl-5 [&>p]:leading-relaxed tabular-nums">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Footer info: tool badge and timestamp */}
        <div
          className={`flex items-center gap-2 text-[11px] text-[#8D8197] px-1 ${
            isUser ? 'justify-end' : 'justify-start'
          }`}
        >
          {message.toolUsed && (
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-[#493653]/40 border border-[#493653]/60 text-[10px] text-[#D19AFF]">
              <Wrench className="w-2.5 h-2.5" />
              <span>{message.toolUsed}</span>
            </span>
          )}
          <time dateTime={message.timestamp.toISOString()}>{formattedTime}</time>
        </div>
      </div>
    </div>
  );
};
