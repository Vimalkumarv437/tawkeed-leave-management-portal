import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export default function DashboardLayout(): React.ReactElement {
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);
  const location = useLocation();

  // Automatically close sidebar when navigation route changes on mobile
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  return (
    <div className="dashboard-layout-root relative min-h-screen bg-slate-50 flex">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="dashboard-main-area flex-1 flex flex-col min-w-0 min-h-screen">
        <Header onToggleSidebar={() => setSidebarOpen((prev) => !prev)} />
        <main className="dashboard-content-body flex-1 p-4 md:p-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
