import React from 'react';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  return (
    <div className="min-h-screen w-full wallpaper-bg flex items-center justify-center p-0 sm:p-3 md:p-5 lg:p-7 overflow-x-hidden">
      {/* 
        Shell Window:
        - 28-34px rounded corners (rounded-[30px]) on medium+ viewports, full height on small screens
        - Translucent dark glassmorphism
        - Bounded max dimensions for large screens (e.g. 1440x900 viewport) so wallpaper shows around edges
      */}
      <div className="w-full h-screen sm:h-[94vh] max-w-[1440px] max-h-[920px] rounded-none sm:rounded-[30px] glass-shell overflow-hidden flex flex-col transition-all duration-200">
        {children}
      </div>
    </div>
  );
};
