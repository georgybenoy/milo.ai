import React from 'react';
import type { LucideIcon } from 'lucide-react';
import { ArrowRight } from 'lucide-react';

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionText: string;
  onClick: () => void;
}

export const FeatureCard: React.FC<FeatureCardProps> = ({
  icon: Icon,
  title,
  description,
  actionText,
  onClick,
}) => {
  return (
    <button
      onClick={onClick}
      className="group flex flex-col justify-between text-left p-4 rounded-2xl bg-[#21172D]/70 hover:bg-[#2B2037] border border-[#493653]/40 hover:border-[#D19AFF]/40 transition-all duration-150 cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#B45BFF] focus:ring-offset-2 focus:ring-offset-[#17121F] shadow-sm hover:shadow-md"
      aria-label={`${title}: ${actionText}`}
    >
      <div className="flex items-center justify-between w-full">
        <div className="p-2 rounded-xl bg-[#2B2037] group-hover:bg-[#493653]/60 text-[#D19AFF] shrink-0 border border-[#493653]/50">
          <Icon className="w-4 h-4" />
        </div>
        <span className="text-[11px] font-medium text-[#8D8197] group-hover:text-[#D19AFF] flex items-center gap-1 transition-colors">
          <span>{actionText}</span>
          <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
        </span>
      </div>
      <div className="mt-3">
        <h4 className="text-xs font-semibold text-[#F6F0FA] group-hover:text-white">
          {title}
        </h4>
        <p className="text-[12px] text-[#B8ACBF] mt-1 leading-relaxed">
          {description}
        </p>
      </div>
    </button>
  );
};
