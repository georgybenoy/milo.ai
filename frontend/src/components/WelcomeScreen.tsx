import React from 'react';
import { Package, TrendingUp, Users, Sparkles } from 'lucide-react';
import { FeatureCard } from './FeatureCard';
import { SuggestedQueryCard } from './SuggestedQueryCard';

interface WelcomeScreenProps {
  onSelectQuery: (query: string) => void;
}

const SUGGESTIONS = [
  {
    title: 'Lookup Specific Order',
    query: 'Where is order ORD-1025?',
    category: 'Status',
  },
  {
    title: 'Cancellation Metrics',
    query: 'How many orders were cancelled?',
    category: 'Analytics',
  },
  {
    title: 'Category Revenue',
    query: 'What was our revenue from Electronics in August 2026?',
    category: 'Revenue',
  },
  {
    title: 'Top Customer Ranking',
    query: 'Who is our top customer by total spend?',
    category: 'Customers',
  },
];

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onSelectQuery }) => {
  return (
    <div className="max-w-3xl mx-auto py-6 px-4 space-y-8 animate-fadeIn">
      {/* Brand Hero */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[#2B2037] border border-[#D19AFF]/30 shadow-lg shadow-[#B45BFF]/10 mb-1">
          <div className="w-7 h-7 rounded-full glowing-orb"></div>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#F6F0FA]">
          Your orders, answered.
        </h1>
        <p className="text-sm text-[#B8ACBF] max-w-lg mx-auto leading-relaxed">
          Ask natural-language questions about orders, revenue breakdowns, top customers, and delivery status.
        </p>
      </div>

      {/* Feature capabilities */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <FeatureCard
          icon={Package}
          title="Order Tracking"
          description="Instant status, items, dates, and amounts for any order."
          badge="Lookup"
        />
        <FeatureCard
          icon={TrendingUp}
          title="Revenue Analytics"
          description="Accurate INR totals filtered by category, month, or city."
          badge="Deterministic"
        />
        <FeatureCard
          icon={Users}
          title="Customer Insights"
          description="Find highest spenders and order volume per customer."
          badge="Rankings"
        />
      </div>

      {/* Suggested prompts */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#8D8197]">
          <Sparkles className="w-3.5 h-3.5 text-[#D19AFF]" />
          <span>Suggested Inquiries</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {SUGGESTIONS.map((item) => (
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
    </div>
  );
};
