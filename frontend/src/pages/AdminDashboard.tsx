import React, { useEffect, useState } from 'react';
import { FileText, Package, Activity, Users } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';

export const AdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({ users: 0, items: 0, logs: 0 });

  useEffect(() => {
    Promise.allSettled([
      api.get('/users'),
      api.get('/logs'),
      api.get('/warehouse/items'),
    ]).then(([u, l, i]) => {
      setStats({
        users: u.status === 'fulfilled' ? (u.value.data?.data?.length || 0) : 0,
        logs: l.status === 'fulfilled' ? (l.value.data?.data?.length || 0) : 0,
        items: i.status === 'fulfilled' ? (i.value.data?.data?.length || 0) : 0,
      });
    });
  }, []);

  const cards = [
    { title: 'Users', value: stats.users, icon: Users, color: 'text-blue-600', bg: 'bg-blue-50' },
    { title: 'Warehouse Items', value: stats.items, icon: Package, color: 'text-pharmacy-600', bg: 'bg-pharmacy-50' },
    { title: 'Audit Logs', value: stats.logs, icon: Activity, color: 'text-purple-600', bg: 'bg-purple-50' },
  ];

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-extrabold text-slate-800">Admin Dashboard</h1>
        <p className="text-slate-500 mt-1">Overview of system metrics</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {cards.map(c => (
          <div key={c.title} className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 flex items-center justify-between">
            <div>
              <p className="text-slate-500 font-medium text-sm mb-1">{c.title}</p>
              <h3 className="text-4xl font-extrabold text-slate-800">{c.value}</h3>
            </div>
            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${c.bg}`}>
              <c.icon className={`w-7 h-7 ${c.color}`} />
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <a href="/admin/documents" className="block bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-2xl shadow-md hover:-translate-y-1 transition-transform">
           <FileText className="w-8 h-8 mb-4 opacity-80" />
           <h3 className="font-bold text-xl mb-1">Documents</h3>
           <p className="text-blue-100 text-sm">Manage SOPs across sections</p>
        </a>
        <a href="/admin/warehouse" className="block bg-gradient-to-br from-pharmacy-500 to-pharmacy-600 text-white p-6 rounded-2xl shadow-md hover:-translate-y-1 transition-transform">
           <Package className="w-8 h-8 mb-4 opacity-80" />
           <h3 className="font-bold text-xl mb-1">Warehouse View</h3>
           <p className="text-pharmacy-100 text-sm">Browse all items and locations</p>
        </a>
        <a href="/admin/logs" className="block bg-gradient-to-br from-purple-500 to-purple-600 text-white p-6 rounded-2xl shadow-md hover:-translate-y-1 transition-transform">
           <Activity className="w-8 h-8 mb-4 opacity-80" />
           <h3 className="font-bold text-xl mb-1">Audit Logs</h3>
           <p className="text-purple-100 text-sm">Track system activities</p>
        </a>
      </div>
    </div>
  );
};
