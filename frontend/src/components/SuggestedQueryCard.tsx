import React from 'react';
import { ArrowUpRight } from 'lucide-react';

interface SuggestedQueryCardProps {
  title: string;
  query: string;
  category?: string;
  onSelect: (query: string) => void;
}

export const SuggestedQueryCard: React.FC<SuggestedQueryCardProps> = ({
  title,
  query,
  category,
  onSelect,
}) => {
  return (
    <button
      onClick={() => onSelect(query)}
      className="group flex flex-col justify-between text-left p-3.5 rounded-2xl bg-[#2B2037]/50 hover:bg-[#2B2037]/90 border border-[#493653]/40 hover:border-[#D19AFF]/40 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-[#B45BFF] focus:ring-offset-2 focus:ring-offset-[#17121F] shadow-sm hover:shadow-md cursor-pointer"
      aria-label={`Ask: ${query}`}
    >
      <div className="flex items-start justify-between gap-2 w-full">
        {category && (
          <span className="text-[11px] font-medium uppercase tracking-wider text-[#D19AFF] bg-[#B45BFF]/10 px-2 py-0.5 rounded-full border border-[#B45BFF]/20">
            {category}
          </span>
        )}
        <ArrowUpRight className="w-4 h-4 text-[#8D8197] group-hover:text-[#D19AFF] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform ml-auto shrink-0" />
      </div>
      <div className="mt-2.5">
        <h4 className="text-xs font-semibold text-[#F6F0FA] group-hover:text-white leading-snug">
          {title}
        </h4>
        <p className="text-[12px] text-[#B8ACBF] mt-1 line-clamp-2">
          &ldquo;{query}&rdquo;
        </p>
      </div>
    </button>
  );
};
