import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onRetry }) => {
  return (
    <div
      role="alert"
      className="flex items-start gap-3 p-4 rounded-2xl bg-[#FF777F]/10 border border-[#FF777F]/30 text-[#F6F0FA] text-sm my-2 max-w-xl"
    >
      <AlertCircle className="w-5 h-5 text-[#FF777F] shrink-0 mt-0.5" aria-hidden="true" />
      <div className="flex-1 space-y-1">
        <p className="font-medium text-[#FF777F]">Unable to complete request</p>
        <p className="text-[#B8ACBF] text-xs leading-relaxed">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[#F6F0FA] bg-[#493653]/60 hover:bg-[#493653] rounded-lg transition-colors border border-[#493653] focus:outline-none focus:ring-2 focus:ring-[#B45BFF]"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Try again
          </button>
        )}
      </div>
    </div>
  );
};
