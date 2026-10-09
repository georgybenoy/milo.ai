import React, { useState } from 'react';
import { Plus, MessageSquare, Database, X, Calendar, Layers, ShieldCheck } from 'lucide-react';
import type { DatasetInfo } from '../types';

interface SidebarProps {
  datasetInfo: DatasetInfo | null;
  datasetLoading: boolean;
  datasetError: string | null;
  onNewChat: () => void;
  isOpenMobile: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  datasetInfo,
  datasetLoading,
  datasetError,
  onNewChat,
  isOpenMobile,
  onCloseMobile,
}) => {
  const [showDatasetModal, setShowDatasetModal] = useState(false);

  // Format date range e.g. "Jun–Sep 2026"
  const formattedDateRange = React.useMemo(() => {
    if (!datasetInfo) return '';
    try {
      const s = new Date(datasetInfo.start_date);
      const e = new Date(datasetInfo.end_date);
      const sMon = s.toLocaleString('default', { month: 'short' });
      const eMon = e.toLocaleString('default', { month: 'short' });
      const year = e.getFullYear();
      return `${sMon}–${eMon} ${year}`;
    } catch {
      return `${datasetInfo.start_date} – ${datasetInfo.end_date}`;
    }
  }, [datasetInfo]);

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpenMobile && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-xs z-40 md:hidden animate-fadeIn"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 w-[260px] bg-[#15111C] border-r border-[#493653]/40 flex flex-col justify-between p-4 transition-transform duration-200 ease-in-out ${
          isOpenMobile ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
        aria-label="Application Sidebar"
      >
        <div className="space-y-6">
          {/* Brand Header */}
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-[#2B2037] border border-[#D19AFF]/30 flex items-center justify-center shadow-md shadow-[#B45BFF]/10 shrink-0">
                <div className="w-4 h-4 rounded-full glowing-orb"></div>
              </div>
              <div>
                <h2 className="text-base font-bold text-[#F6F0FA] tracking-tight leading-none">
                  Milo
                </h2>
                <p className="text-[11px] text-[#8D8197] font-medium tracking-wide mt-1">
                  Order intelligence
                </p>
              </div>
            </div>

            {/* Mobile Close Button */}
            <button
              onClick={onCloseMobile}
              className="md:hidden p-1.5 rounded-lg text-[#8D8197] hover:text-[#F6F0FA] hover:bg-[#2B2037]"
              aria-label="Close sidebar"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* New Chat Button */}
          <button
            onClick={() => {
              onNewChat();
              onCloseMobile();
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-[#B45BFF]/15 hover:bg-[#B45BFF]/25 text-[#D19AFF] hover:text-[#F6F0FA] border border-[#B45BFF]/30 text-xs font-semibold transition-all duration-150 cursor-pointer shadow-xs focus:outline-none focus:ring-2 focus:ring-[#B45BFF]"
          >
            <Plus className="w-4 h-4" />
            <span>New Chat</span>
          </button>

          {/* Navigation - Chat is the only nav item */}
          <nav className="space-y-1" aria-label="Main Navigation">
            <button
              className="w-full flex items-center gap-3 px-3 py-2 rounded-xl bg-[#2B2037]/70 text-[#F6F0FA] text-xs font-medium border border-[#493653]/50 cursor-pointer text-left"
              aria-current="page"
            >
              <MessageSquare className="w-4 h-4 text-[#D19AFF]" />
              <span>Chat</span>
            </button>
          </nav>
        </div>

        {/* Bottom Section: Order Dataset Card */}
        <div className="pt-4 border-t border-[#493653]/30">
          <div
            onClick={() => setShowDatasetModal(true)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                setShowDatasetModal(true);
              }
            }}
            className="group p-3 rounded-xl bg-[#21172D]/70 hover:bg-[#2B2037] border border-[#493653]/40 hover:border-[#D19AFF]/30 transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#B45BFF]"
            aria-label="View dataset details"
          >
            <div className="flex items-center gap-2 text-xs font-semibold text-[#F6F0FA]">
              <Database className="w-3.5 h-3.5 text-[#D19AFF]" />
              <span>Order Dataset</span>
            </div>

            {datasetLoading ? (
              <div className="mt-2 space-y-1.5 animate-pulse">
                <div className="h-3 bg-[#493653]/50 rounded w-3/4"></div>
                <div className="h-2.5 bg-[#493653]/30 rounded w-1/2"></div>
              </div>
            ) : datasetError ? (
              <p className="mt-1.5 text-[11px] text-[#FF777F]">
                Dataset offline
              </p>
            ) : datasetInfo ? (
              <p className="mt-1 text-[11px] text-[#B8ACBF] tabular-nums leading-relaxed">
                <span className="font-semibold text-[#F6F0FA]">{datasetInfo.record_count}</span> orders · {formattedDateRange}
              </p>
            ) : null}
          </div>
        </div>
      </aside>

      {/* Dataset Details Popover / Modal */}
      {showDatasetModal && datasetInfo && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="dataset-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs animate-fadeIn"
          onClick={() => setShowDatasetModal(false)}
        >
          <div
            className="w-full max-w-sm rounded-2xl bg-[#17121F] border border-[#493653] p-5 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-2 border-b border-[#493653]/40">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-[#D19AFF]" />
                <h3 id="dataset-modal-title" className="text-sm font-bold text-[#F6F0FA]">
                  Dataset Metadata
                </h3>
              </div>
              <button
                onClick={() => setShowDatasetModal(false)}
                className="text-[#8D8197] hover:text-[#F6F0FA] p-1 rounded-lg"
                aria-label="Close modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#21172D] border border-[#493653]/30">
                <span className="text-[#8D8197] flex items-center gap-2">
                  <Layers className="w-3.5 h-3.5 text-[#B45BFF]" />
                  Total Orders
                </span>
                <span className="font-semibold text-[#F6F0FA] tabular-nums">
                  {datasetInfo.record_count} verified rows
                </span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#21172D] border border-[#493653]/30">
                <span className="text-[#8D8197] flex items-center gap-2">
                  <Calendar className="w-3.5 h-3.5 text-[#6E9BFF]" />
                  Date Range
                </span>
                <span className="font-semibold text-[#F6F0FA] tabular-nums">
                  {datasetInfo.start_date} → {datasetInfo.end_date}
                </span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#21172D] border border-[#493653]/30">
                <span className="text-[#8D8197] flex items-center gap-2">
                  <ShieldCheck className="w-3.5 h-3.5 text-[#53D6A0]" />
                  Data Integrity
                </span>
                <span className="font-semibold text-[#53D6A0]">
                  100% Deterministic
                </span>
              </div>
            </div>

            <button
              onClick={() => setShowDatasetModal(false)}
              className="w-full py-2 text-xs font-semibold rounded-xl bg-[#2B2037] hover:bg-[#493653] text-[#F6F0FA] border border-[#493653] transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </>
  );
};
