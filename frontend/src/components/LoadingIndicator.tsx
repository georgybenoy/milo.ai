import React from 'react';

interface LoadingIndicatorProps {
  message?: string;
}

export const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({
  message = 'Analysing orders...',
}) => {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center gap-3 py-3 px-4 rounded-2xl bg-[#2B2037]/60 border border-[#493653]/50 text-[#B8ACBF] text-sm w-fit animate-pulse"
    >
      <div className="flex items-center gap-1.5" aria-hidden="true">
        <span className="w-2 h-2 rounded-full bg-[#B45BFF] animate-bounce [animation-delay:-0.3s]"></span>
        <span className="w-2 h-2 rounded-full bg-[#D19AFF] animate-bounce [animation-delay:-0.15s]"></span>
        <span className="w-2 h-2 rounded-full bg-[#6E9BFF] animate-bounce"></span>
      </div>
      <span className="font-medium">{message}</span>
    </div>
  );
};
