import React from 'react';
import { useAuth } from '../hooks/useAuth';
import { UserCircle, ShieldCheck, Menu } from 'lucide-react';

interface HeaderProps {
  onToggleSidebar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
  const { user, section } = useAuth();

  return (
    <header className="h-20 bg-white/80 backdrop-blur-md border-b border-slate-200 px-4 lg:px-8 flex items-center justify-between sticky top-0 z-40 shadow-sm">
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 -ml-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors"
          title="Open menu"
        >
          <Menu className="w-6 h-6" />
        </button>
        {user?.role === 'EMPLOYEE' && section && (
          <div className="flex items-center gap-2 bg-pharmacy-50 px-3 py-1.5 rounded-lg border border-pharmacy-100">
            <span className="w-2 h-2 rounded-full bg-pharmacy-500 animate-pulse"></span>
            <span className="text-sm font-semibold text-pharmacy-700">Section: {section.name}</span>
          </div>
        )}
        {user?.role === 'ADMIN' && (
          <div className="flex items-center gap-2 bg-blue-50 px-3 py-1.5 rounded-lg border border-blue-100">
            <ShieldCheck className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-semibold text-blue-700">Administrator</span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        <div className="text-right">
          <p className="text-sm font-bold text-slate-800">{user?.username}</p>
          <p className="text-xs text-slate-500 capitalize">{user?.role.toLowerCase()}</p>
        </div>
        <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center border border-slate-200 text-slate-500">
          <UserCircle className="w-6 h-6" />
        </div>
      </div>
    </header>
  );
};
