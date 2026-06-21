import React, { useEffect, useState, useCallback } from 'react';
import {
  Activity, Loader2, Search, User, Clock,
  RefreshCw, FileText, ArrowRightLeft, LogIn,
  LogOut, Upload, Trash2, Package, Eye, ChevronDown
} from 'lucide-react';
import api from '../services/api';

// ── Action colour + icon map ──────────────────────────────────────────────────
const ACTION_META: Record<string, { color: string; bg: string; icon: React.ReactNode }> = {
  LOGIN:           { color: 'text-green-700',  bg: 'bg-green-50 border-green-100',  icon: <LogIn  className="w-3 h-3" /> },
  LOGOUT:          { color: 'text-slate-600',  bg: 'bg-slate-50 border-slate-100',  icon: <LogOut className="w-3 h-3" /> },
  OPEN_DOCUMENT:   { color: 'text-blue-700',   bg: 'bg-blue-50 border-blue-100',    icon: <Eye    className="w-3 h-3" /> },
  UPLOAD_DOCUMENT: { color: 'text-teal-700',   bg: 'bg-teal-50 border-teal-100',    icon: <Upload className="w-3 h-3" /> },
  ARCHIVE_DOCUMENT:{ color: 'text-orange-700', bg: 'bg-orange-50 border-orange-100',icon: <FileText className="w-3 h-3" /> },
  DELETE:          { color: 'text-red-700',    bg: 'bg-red-50 border-red-100',      icon: <Trash2 className="w-3 h-3" /> },
  MOVE_ITEM:       { color: 'text-purple-700', bg: 'bg-purple-50 border-purple-100',icon: <ArrowRightLeft className="w-3 h-3" /> },
  ADD_ITEM:        { color: 'text-indigo-700', bg: 'bg-indigo-50 border-indigo-100',icon: <Package className="w-3 h-3" /> },
  SEARCH_ITEM:     { color: 'text-sky-700',    bg: 'bg-sky-50 border-sky-100',      icon: <Search className="w-3 h-3" /> },
  UPDATE:          { color: 'text-amber-700',  bg: 'bg-amber-50 border-amber-100',  icon: <RefreshCw className="w-3 h-3" /> },
};

const MODULE_COLOR: Record<string, string> = {
  IAM:       'bg-blue-100 text-blue-700',
  SOP:       'bg-teal-100 text-teal-700',
  WAREHOUSE: 'bg-purple-100 text-purple-700',
  SYSTEM:    'bg-slate-100 text-slate-600',
};

const LIMITS = [50, 100, 250, 500];

export const AdminLogs: React.FC = () => {
  const [logs, setLogs]         = useState<any[]>([]);
  const [loading, setLoading]   = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch]     = useState('');
  const [actionFilter, setActionFilter] = useState('ALL');
  const [moduleFilter, setModuleFilter] = useState('ALL');
  const [limit, setLimit]       = useState(100);
  const [expanded, setExpanded] = useState<string | null>(null);

  const fetchLogs = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);
    try {
      const res = await api.get(`/logs?limit=${limit}`);
      setLogs(res.data?.data || []);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [limit]);

  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  // Collect unique actions + modules for filter dropdowns
  const allActions = ['ALL', ...Array.from(new Set(logs.map(l => l.action))).sort()];
  const allModules = ['ALL', ...Array.from(new Set(logs.map(l => l.module || l.resource_type || 'SYSTEM'))).sort()];

  const filtered = logs.filter(l => {
    const text = `${l.username} ${l.action} ${l.module} ${l.description || ''}`.toLowerCase();
    const matchSearch = !search || text.includes(search.toLowerCase());
    const matchAction = actionFilter === 'ALL' || l.action === actionFilter;
    const matchModule = moduleFilter === 'ALL' || (l.module || l.resource_type) === moduleFilter;
    return matchSearch && matchAction && matchModule;
  });

  const actionMeta = (action: string) =>
    ACTION_META[action] ?? { color: 'text-slate-600', bg: 'bg-slate-50 border-slate-100', icon: <Activity className="w-3 h-3" /> };

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex flex-wrap justify-between items-start gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-800 flex items-center gap-3">
            <span className="p-2 bg-blue-100 text-blue-600 rounded-xl"><Activity className="w-6 h-6" /></span>
            Audit Logs
          </h1>
          <p className="text-slate-500 mt-1">System activity and security events</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500 font-medium">{filtered.length} events</span>
          <button
            onClick={() => fetchLogs(true)}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-white border-2 border-slate-200 rounded-xl text-slate-600 hover:border-pharmacy-400 hover:text-pharmacy-600 font-medium text-sm transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </header>

      {/* Filters */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
        <div className="flex flex-wrap gap-3 items-center">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search user, action, description…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500 text-sm"
            />
          </div>

          {/* Action filter */}
          <div className="relative">
            <select
              value={actionFilter}
              onChange={e => setActionFilter(e.target.value)}
              className="appearance-none pl-3 pr-8 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500 text-sm font-medium bg-white cursor-pointer"
            >
              {allActions.map(a => <option key={a} value={a}>{a === 'ALL' ? 'All Actions' : a}</option>)}
            </select>
            <ChevronDown className="w-3 h-3 absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          </div>

          {/* Module filter */}
          <div className="relative">
            <select
              value={moduleFilter}
              onChange={e => setModuleFilter(e.target.value)}
              className="appearance-none pl-3 pr-8 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500 text-sm font-medium bg-white cursor-pointer"
            >
              {allModules.map(m => <option key={m} value={m}>{m === 'ALL' ? 'All Modules' : m}</option>)}
            </select>
            <ChevronDown className="w-3 h-3 absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          </div>

          {/* Limit */}
          <div className="relative">
            <select
              value={limit}
              onChange={e => setLimit(Number(e.target.value))}
              className="appearance-none pl-3 pr-8 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500 text-sm font-medium bg-white cursor-pointer"
            >
              {LIMITS.map(l => <option key={l} value={l}>Last {l}</option>)}
            </select>
            <ChevronDown className="w-3 h-3 absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        {loading ? (
          <div className="p-12 flex flex-col items-center gap-3 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-pharmacy-500" />
            <p className="text-sm">Loading audit trail…</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 text-slate-400 text-xs font-bold uppercase tracking-wider border-b border-slate-100">
                <tr>
                  <th className="px-5 py-3">User</th>
                  <th className="px-5 py-3">Action</th>
                  <th className="px-5 py-3">Module</th>
                  <th className="px-5 py-3">Description</th>
                  <th className="px-5 py-3 whitespace-nowrap">IP Address</th>
                  <th className="px-5 py-3 whitespace-nowrap">Time</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-12 text-center text-slate-400">
                      <Activity className="w-8 h-8 mx-auto mb-2 opacity-30" />
                      <p>No log entries found.</p>
                    </td>
                  </tr>
                ) : (
                  filtered.map((l, i) => {
                    const meta = actionMeta(l.action);
                    const moduleColor = MODULE_COLOR[l.module || l.resource_type] ?? 'bg-slate-100 text-slate-600';
                    const isExpanded = expanded === (l.id || String(i));
                    const desc = l.description || '';

                    return (
                      <tr
                        key={l.id || i}
                        onClick={() => setExpanded(isExpanded ? null : (l.id || String(i)))}
                        className={`border-b border-slate-50 cursor-pointer transition-colors ${isExpanded ? 'bg-slate-50' : 'hover:bg-slate-50/60'}`}
                      >
                        {/* User */}
                        <td className="px-5 py-3.5">
                          <div className="flex items-center gap-2 font-medium text-slate-700">
                            <div className="w-7 h-7 bg-gradient-to-br from-pharmacy-400 to-pharmacy-600 rounded-full flex items-center justify-center flex-shrink-0">
                              <User className="w-3.5 h-3.5 text-white" />
                            </div>
                            <span className="font-mono text-xs">{l.username || '—'}</span>
                          </div>
                        </td>

                        {/* Action */}
                        <td className="px-5 py-3.5">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-bold ${meta.bg} ${meta.color}`}>
                            {meta.icon}
                            {l.action}
                          </span>
                        </td>

                        {/* Module */}
                        <td className="px-5 py-3.5">
                          <span className={`px-2.5 py-1 rounded-lg text-xs font-bold ${moduleColor}`}>
                            {l.module || l.resource_type || 'SYSTEM'}
                          </span>
                        </td>

                        {/* Description */}
                        <td className="px-5 py-3.5 text-slate-600 max-w-xs">
                          <span className={`block text-xs ${isExpanded ? 'whitespace-normal' : 'truncate'}`} title={desc}>
                            {desc || <span className="text-slate-300 italic">—</span>}
                          </span>
                        </td>

                        {/* IP */}
                        <td className="px-5 py-3.5">
                          <span className="font-mono text-xs text-slate-400">{l.ip_address || '—'}</span>
                        </td>

                        {/* Time */}
                        <td className="px-5 py-3.5">
                          <div className="flex items-center gap-1 text-slate-500 text-xs whitespace-nowrap">
                            <Clock className="w-3 h-3 flex-shrink-0" />
                            {new Date(l.timestamp || l.created_at).toLocaleString()}
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Footer count */}
      {!loading && filtered.length > 0 && (
        <p className="text-xs text-slate-400 text-center">
          Showing {filtered.length} of {logs.length} total events — click any row to expand description
        </p>
      )}
    </div>
  );
};
