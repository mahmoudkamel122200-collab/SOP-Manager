import React, { useState } from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Sidebar } from '../components/Sidebar';
import { Header } from '../components/Header';
import { motion } from 'framer-motion';

export const DashboardLayout: React.FC<{ allowedRole?: 'ADMIN' | 'EMPLOYEE' }> = ({ allowedRole }) => {
  const { user, loading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-lab-light">
        <div className="w-16 h-16 border-4 border-pharmacy-200 border-t-pharmacy-600 rounded-full animate-spin"></div>
        <p className="mt-4 text-slate-500 font-medium animate-pulse">Loading workspace...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRole === 'ADMIN' && user.role !== 'ADMIN') {
    return <Navigate to="/employee/dashboard" replace />;
  }

  return (
    <div className="min-h-screen flex overflow-hidden relative bg-transparent">
      {/* Background elements */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-pharmacy-50/40 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3"></div>
        <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-blue-50/40 rounded-full blur-3xl translate-y-1/3 -translate-x-1/3"></div>
      </div>

      {/* Sidebar overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 lg:ml-64 flex flex-col h-screen overflow-hidden z-10 relative">
        <Header onToggleSidebar={() => setSidebarOpen(true)} />
        <motion.main
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex-1 overflow-y-auto p-4 md:p-8"
        >
          <div className="max-w-6xl mx-auto">
            <Outlet />
          </div>
        </motion.main>
      </div>
    </div>
  );
};
