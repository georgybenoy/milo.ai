import React from 'react';
import { Menu, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import type { HealthStatus } from '../types';

interface HeaderProps {
  healthStatus: HealthStatus;
  dataLoaded: boolean;
  onOpenMobileMenu: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  healthStatus,
  dataLoaded,
  onOpenMobileMenu,
}) => {
  // Determine status display
  let statusText = 'Connecting';
  let badgeColor = 'bg-[#F2C66D]/15 text-[#F2C66D] border-[#F2C66D]/30';
  let StatusIcon = AlertTriangle;

  if (healthStatus === 'ready' && dataLoaded) {
    statusText = 'Ready';
    badgeColor = 'bg-[#53D6A0]/15 text-[#53D6A0] border-[#53D6A0]/30';
    StatusIcon = CheckCircle2;
  } else if (healthStatus === 'unavailable') {
    statusText = 'Unavailable';
    badgeColor = 'bg-[#FF777F]/15 text-[#FF777F] border-[#FF777F]/30';
    StatusIcon = XCircle;
  }

  return (
    <header className="flex items-center justify-between px-4 sm:px-6 py-3.5 border-b border-[#493653]/40 bg-[#17121F]/60 backdrop-blur-md">
      <div className="flex items-center gap-3">
        {/* Mobile menu trigger */}
        <button
          onClick={onOpenMobileMenu}
          aria-label="Open navigation sidebar"
          className="md:hidden p-2 rounded-xl text-[#B8ACBF] hover:text-[#F6F0FA] hover:bg-[#2B2037] focus:outline-none focus:ring-2 focus:ring-[#B45BFF]"
        >
          <Menu className="w-5 h-5" />
        </button>
      </div>

      {/* Real-time Status Indicator */}
      <div
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${badgeColor} transition-colors`}
        title={`Backend status: ${statusText}`}
      >
        <span className={`w-2 h-2 rounded-full ${statusText === 'Ready' ? 'bg-[#53D6A0]' : statusText === 'Connecting' ? 'bg-[#F2C66D] animate-ping' : 'bg-[#FF777F]'}`}></span>
        <StatusIcon className="w-3.5 h-3.5" />
        <span>{statusText}</span>
      </div>
    </header>
  );
};
