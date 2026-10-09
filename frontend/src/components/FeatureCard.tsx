import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  badge?: string;
}

export const FeatureCard: React.FC<FeatureCardProps> = ({
  icon: Icon,
  title,
  description,
  badge,
}) => {
  return (
    <div className="flex items-start gap-3.5 p-3.5 rounded-2xl bg-[#21172D]/60 border border-[#493653]/30">
      <div className="p-2 rounded-xl bg-[#2B2037] text-[#D19AFF] shrink-0 border border-[#493653]/50">
        <Icon className="w-4 h-4" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h4 className="text-xs font-semibold text-[#F6F0FA]">{title}</h4>
          {badge && (
            <span className="text-[10px] font-medium text-[#6E9BFF] bg-[#6E9BFF]/10 px-1.5 py-0.5 rounded-md border border-[#6E9BFF]/20">
              {badge}
            </span>
          )}
        </div>
        <p className="text-[12px] text-[#8D8197] mt-0.5 leading-relaxed">{description}</p>
      </div>
    </div>
  );
};
