import React, { useState, useEffect } from 'react';
import {
  Layers, Plus, Trash2, Loader2, Users,
  FileText, ChevronRight, X, Check, AlertCircle
} from 'lucide-react';
import api from '../services/api';

interface Section {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

export const AdminSections: React.FC = () => {
  const [sections, setSections] = useState<Section[]>([]);
  const [loading, setLoading]   = useState(true);

  // Create form
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName]       = useState('');
  const [newDesc, setNewDesc]       = useState('');
  const [creating, setCreating]     = useState(false);
  const [createError, setCreateError] = useState('');

  // Delete confirm
  const [confirmSec, setConfirmSec] = useState<Section | null>(null);
  const [deleting, setDeleting]     = useState(false);
  const [deleteError, setDeleteError] = useState('');

  // Toast
  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 3500);
  };

  const fetchSections = async () => {
    setLoading(true);
    try {
      const res = await api.get('/sections');
      setSections(res.data?.data || []);
    } catch {
      showToast('error', 'Failed to load sections.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSections(); }, []);

  // ── Create ──────────────────────────────────────────────────────────────────
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    setCreateError('');
    try {
      await api.post('/sections', { name: newName.trim(), description: newDesc.trim() || null });
      setShowCreate(false);
      setNewName('');
      setNewDesc('');
      showToast('success', `Section "${newName.trim()}" created successfully.`);
      fetchSections();
    } catch (e: any) {
      setCreateError(e.response?.data?.message || e.response?.data?.detail || e.message || 'Create failed.');
    } finally {
      setCreating(false);
    }
  };

  // ── Delete ──────────────────────────────────────────────────────────────────
  const handleDelete = async () => {
    if (!confirmSec) return;
    setDeleting(true);
    setDeleteError('');
    try {
      await api.delete(`/sections/${confirmSec.id}`);
      setSections(prev => prev.filter(s => s.id !== confirmSec.id));
      showToast('success', `Section "${confirmSec.name}" deleted.`);
      setConfirmSec(null);
    } catch (e: any) {
      setDeleteError(e.response?.data?.message || e.response?.data?.detail || e.message || 'Delete failed.');
    } finally {
      setDeleting(false);
    }
  };

  // Section colour palette (cycles)
  const COLORS = [
    'from-teal-400 to-cyan-500',
    'from-blue-400 to-indigo-500',
    'from-violet-400 to-purple-500',
    'from-rose-400 to-pink-500',
    'from-amber-400 to-orange-500',
    'from-emerald-400 to-green-500',
  ];

  return (
    <div className="space-y-6">

      {/* ── Toast ──────────────────────────────────────────────────────────── */}
      {toast && (
        <div className={`fixed top-6 right-6 z-[100] flex items-center gap-3 px-5 py-4 rounded-2xl shadow-xl text-sm font-semibold transition-all
          ${toast.type === 'success'
            ? 'bg-green-600 text-white'
            : 'bg-red-600 text-white'}`}
        >
          {toast.type === 'success'
            ? <Check className="w-4 h-4 flex-shrink-0" />
            : <AlertCircle className="w-4 h-4 flex-shrink-0" />}
          {toast.msg}
        </div>
      )}

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-800 flex items-center gap-3">
            <span className="p-2 bg-teal-100 text-teal-600 rounded-xl">
              <Layers className="w-6 h-6" />
            </span>
            Sections
          </h1>
          <p className="text-slate-500 mt-1">Manage factory sections and their access</p>
        </div>
        <button
          type="button"
          onClick={() => { setShowCreate(true); setCreateError(''); }}
          className="bg-pharmacy-600 hover:bg-pharmacy-700 text-white px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 shadow-md transition-colors"
        >
          <Plus className="w-4 h-4" /> New Section
        </button>
      </header>

      {/* ── Create Modal ────────────────────────────────────────────────────── */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-xl font-bold text-slate-800">Create New Section</h2>
                <p className="text-sm text-slate-500 mt-0.5">Add a new factory section to the system</p>
              </div>
              <button
                type="button"
                onClick={() => { setShowCreate(false); setCreateError(''); }}
                className="p-2 rounded-xl hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-1.5 text-slate-700">
                  Section Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={e => setNewName(e.target.value)}
                  placeholder="e.g. Quality Control, R&D Lab…"
                  className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500 transition-colors"
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1.5 text-slate-700">
                  Description <span className="text-slate-400 font-normal">(optional)</span>
                </label>
                <textarea
                  rows={3}
                  value={newDesc}
                  onChange={e => setNewDesc(e.target.value)}
                  placeholder="Brief description of this section's role…"
                  className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500 transition-colors resize-none"
                />
              </div>

              {createError && (
                <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-100 px-4 py-3 rounded-xl">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {createError}
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => { setShowCreate(false); setCreateError(''); }}
                  className="flex-1 py-2.5 rounded-xl border-2 border-slate-200 font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating || !newName.trim()}
                  className="flex-1 py-2.5 rounded-xl bg-pharmacy-600 hover:bg-pharmacy-700 text-white font-medium flex items-center justify-center gap-2 transition-colors disabled:opacity-60"
                >
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                  {creating ? 'Creating…' : 'Create Section'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Delete Confirm Modal ────────────────────────────────────────────── */}
      {confirmSec && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-8 max-w-sm w-full shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-red-100 rounded-xl">
                <Trash2 className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-800">Delete Section</h2>
                <p className="text-sm text-slate-500">This will remove all section access</p>
              </div>
            </div>
            <p className="text-slate-600 mb-2 text-sm">Are you sure you want to delete:</p>
            <p className="font-bold text-slate-800 bg-slate-50 border border-slate-200 px-4 py-3 rounded-xl mb-1 text-lg">
              {confirmSec.name}
            </p>
            {confirmSec.description && (
              <p className="text-xs text-slate-500 mb-3 px-1">{confirmSec.description}</p>
            )}
            <p className="text-xs text-amber-600 bg-amber-50 border border-amber-100 px-3 py-2 rounded-lg mb-4 flex items-start gap-2">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
              Documents and user assignments linked to this section will be affected.
            </p>

            {deleteError && (
              <p className="text-red-600 text-sm bg-red-50 border border-red-100 px-3 py-2 rounded-lg mb-4">
                {deleteError}
              </p>
            )}

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => { setConfirmSec(null); setDeleteError(''); }}
                disabled={deleting}
                className="flex-1 py-2.5 rounded-xl border-2 border-slate-200 font-medium text-slate-600 hover:bg-slate-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleting}
                className="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-medium flex items-center justify-center gap-2 transition-colors disabled:opacity-60"
              >
                {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                {deleting ? 'Deleting…' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Sections Grid ───────────────────────────────────────────────────── */}
      {loading ? (
        <div className="flex justify-center items-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-pharmacy-500" />
        </div>
      ) : sections.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-16 flex flex-col items-center gap-4 text-slate-400">
          <Layers className="w-12 h-12 opacity-30" />
          <p className="font-medium">No sections yet. Create your first section.</p>
          <button
            type="button"
            onClick={() => setShowCreate(true)}
            className="mt-2 px-5 py-2.5 bg-pharmacy-600 text-white rounded-xl font-medium hover:bg-pharmacy-700 transition-colors flex items-center gap-2"
          >
            <Plus className="w-4 h-4" /> New Section
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {sections.map((sec, idx) => {
            const gradient = COLORS[idx % COLORS.length];
            return (
              <div
                key={sec.id}
                className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow group"
              >
                {/* Colour strip */}
                <div className={`h-2 w-full bg-gradient-to-r ${gradient}`} />

                <div className="p-5">
                  <div className="flex justify-between items-start">
                    <div className={`p-2.5 rounded-xl bg-gradient-to-br ${gradient} shadow-sm`}>
                      <Layers className="w-5 h-5 text-white" />
                    </div>
                    <button
                      type="button"
                      onClick={e => { e.stopPropagation(); setDeleteError(''); setConfirmSec(sec); }}
                      className="opacity-0 group-hover:opacity-100 p-2 rounded-xl text-red-400 hover:text-red-600 hover:bg-red-50 transition-all"
                      title="Delete section"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <h3 className="font-bold text-slate-800 text-lg mt-3">{sec.name}</h3>
                  <p className="text-slate-500 text-sm mt-1 min-h-[2.5rem] line-clamp-2">
                    {sec.description || <span className="italic text-slate-300">No description</span>}
                  </p>

                  <div className="mt-4 pt-4 border-t border-slate-50 flex items-center justify-between text-xs text-slate-400">
                    <span>
                      Created {new Date(sec.created_at).toLocaleDateString()}
                    </span>
                    <ChevronRight className="w-4 h-4" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Summary */}
      {!loading && sections.length > 0 && (
        <div className="flex items-center gap-6 text-sm text-slate-400 pt-2">
          <span className="flex items-center gap-1.5">
            <Layers className="w-4 h-4" />
            {sections.length} section{sections.length !== 1 ? 's' : ''}
          </span>
          <span className="flex items-center gap-1.5">
            <Users className="w-4 h-4" />
            Assign users in the Users panel
          </span>
          <span className="flex items-center gap-1.5">
            <FileText className="w-4 h-4" />
            Documents → per section
          </span>
        </div>
      )}
    </div>
  );
};
