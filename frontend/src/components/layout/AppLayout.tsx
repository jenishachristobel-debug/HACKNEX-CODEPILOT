import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export const AppLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#F7F8FC]">
      <Sidebar />
      <Topbar />
      <main className="ml-64 pt-16 min-h-screen p-8">
        <Outlet />
      </main>
    </div>
  );
};

