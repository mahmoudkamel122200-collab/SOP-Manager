import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Package,
  Activity,
  FlaskConical,
  Layers,
  Users,
  LogOut,
  X
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const isEmployeeView = location.pathname.startsWith('/employee');

  const adminLinks = [
    { name: 'Dashboard', path: '/admin/dashboard', icon: LayoutDashboard },
    { name: 'Sections',  path: '/admin/sections',  icon: Layers },
    { name: 'Users',     path: '/admin/users',     icon: Users },
    { name: 'Documents', path: '/admin/documents', icon: FileText },
    { name: 'Warehouse', path: '/admin/warehouse', icon: Package },
    { name: 'Audit Logs', path: '/admin/logs',     icon: Activity },
  ];

  const employeeLinks = [
    { name: 'Workspace', path: '/employee/dashboard', icon: LayoutDashboard },
  ];

  const links = (user?.role === 'ADMIN' && !isEmployeeView) ? adminLinks : employeeLinks;

  return (
    <aside className={`w-64 h-screen bg-white border-r border-slate-200 fixed left-0 top-0 flex flex-col z-50 shadow-sm transition-transform duration-300 ease-in-out lg:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="h-20 flex items-center justify-between px-6 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pharmacy-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-pharmacy-500/30 text-white">
            <FlaskConical className="w-6 h-6" />
          </div>
          <div>
            <span className="font-bold text-lg text-slate-800 tracking-tight leading-none block">PharmaSys</span>
            <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Management</span>
          </div>
        </div>
        <button onClick={onClose} className="lg:hidden p-1.5 text-slate-500 hover:bg-slate-100 rounded-lg">
          <X className="w-5 h-5" />
        </button>
      </div>

      <nav className="flex-1 py-6 px-4 flex flex-col gap-2 overflow-y-auto">
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink
              key={link.path}
              to={link.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                  isActive
                    ? 'bg-pharmacy-500 text-white shadow-md shadow-pharmacy-500/20 font-medium'
                    : 'text-slate-600 hover:bg-pharmacy-50 hover:text-pharmacy-700 font-medium'
                }`
              }
            >
              <Icon className="w-5 h-5" />
              <span>{link.name}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-100">
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-slate-600 hover:bg-red-50 hover:text-red-600 font-medium transition-colors"
        >
          <LogOut className="w-5 h-5" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};
