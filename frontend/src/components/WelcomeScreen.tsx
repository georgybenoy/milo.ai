import React from 'react';
import { Package, TrendingUp, Users, Sparkles } from 'lucide-react';
import { FeatureCard } from './FeatureCard';
import { SuggestedQueryCard } from './SuggestedQueryCard';

interface WelcomeScreenProps {
  onSelectQuery: (query: string) => void;
  onFocusComposer?: (prefill?: string) => void;
}

const FOUR_SUGGESTIONS = [
  {
    title: 'Find an order',
    query: 'What is the status of order ORD-1025?',
    category: 'Status',
  },
  {
    title: 'Cancelled orders',
    query: 'How many orders were cancelled?',
    category: 'Count',
  },
  {
    title: 'August revenue',
    query: 'What was the total revenue from Electronics in August?',
    category: 'Revenue',
  },
  {
    title: 'Top customer',
    query: 'Which customer has spent the most?',
    category: 'Ranking',
  },
];

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  onSelectQuery,
  onFocusComposer,
}) => {
  return (
    <div className="max-w-4xl mx-auto py-4 sm:py-8 px-2 sm:px-4 space-y-7 animate-fadeIn">
      {/* Brand Hero */}
      <div className="text-center space-y-3.5">
        <div className="inline-flex items-center justify-center p-2.5 rounded-2xl mb-1 bg-[#2B2037]/50 border border-[#D19AFF]/30 shadow-[0_8px_32px_rgba(180,91,255,0.25)] backdrop-blur-md">
          <img
            src="/milo-logo-transparent.png"
            alt="Milo Logo"
            className="w-16 h-16 sm:w-20 sm:h-20 object-contain drop-shadow-[0_4px_16px_rgba(180,91,255,0.4)]"
          />
        </div>
        <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold tracking-tight text-[#F6F0FA]">
          Your orders, <span className="text-[#D19AFF]">answered.</span>
        </h1>
        <p className="text-sm sm:text-base text-[#B8ACBF] max-w-lg mx-auto leading-relaxed">
          Ask about order status, revenue, and customer spending.
        </p>
      </div>

      {/* Four Suggested Query Cards (Single row on desktop, wrapping on smaller screens) */}
      <div className="space-y-2.5">
        <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-[#8D8197] px-1">
          <Sparkles className="w-3.5 h-3.5 text-[#D19AFF]" />
          <span>Suggested Questions</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {FOUR_SUGGESTIONS.map((item) => (
            <SuggestedQueryCard
              key={item.query}
              title={item.title}
              query={item.query}
              category={item.category}
              onSelect={onSelectQuery}
            />
          ))}
        </div>
      </div>

      {/* Three Feature Cards with real interactive behavior */}
      <div className="space-y-2.5 pt-1">
        <div className="text-xs font-semibold uppercase tracking-wider text-[#8D8197] px-1">
          <span>Capabilities</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <FeatureCard
            icon={Package}
            title="Order Lookup"
            description="Query any order by its identifier to inspect status, items, date, and customer."
            actionText="Check order"
            onClick={() => {
              if (onFocusComposer) {
                onFocusComposer('What is the status of order ORD-');
              } else {
                onSelectQuery('What is the status of order ORD-1025?');
              }
            }}
          />
          <FeatureCard
            icon={TrendingUp}
            title="Revenue Analysis"
            description="Calculate exact revenue totals deterministically across categories, months, or cities."
            actionText="Sum revenue"
            onClick={() => onSelectQuery('What was the total revenue across all orders?')}
          />
          <FeatureCard
            icon={Users}
            title="Customer Insights"
            description="Identify top spenders and review aggregated customer transaction history."
            actionText="View ranking"
            onClick={() => onSelectQuery('Which customer has spent the most?')}
          />
        </div>
      </div>
    </div>
  );
};
