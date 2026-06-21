import React, { useState, useEffect, useRef } from 'react';
import { FileText, Trash2, Loader2, Plus } from 'lucide-react';
import api from '../services/api';

export const AdminDocuments: React.FC = () => {
  const [documents, setDocuments] = useState<any[]>([]);
  const [sections, setSections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Upload Form
  const [showUpload, setShowUpload] = useState(false);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadDesc, setUploadDesc] = useState('');
  const [uploadSection, setUploadSection] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  // Delete confirm modal
  const [confirmDoc, setConfirmDoc] = useState<{ id: string; title: string } | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const secRes = await api.get('/sections');
      const secs = secRes.data?.data || [];
      setSections(secs);
      if (secs.length > 0) setUploadSection(secs[0].id);

      const allDocs: any[] = [];
      for (const s of secs) {
        try {
          const dRes = await api.get(`/documents/section/${s.id}`);
          const docs = dRes.data?.data?.documents || [];
          docs.forEach((d: any) => allDocs.push({ ...d, section_name: s.name }));
        } catch (e) {}
      }
      setDocuments(allDocs);
    } catch (e) {}
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    setUploading(true);
    const fd = new FormData();
    fd.append('title', uploadTitle);
    fd.append('description', uploadDesc);
    fd.append('section_id', uploadSection);
    fd.append('file', uploadFile);

    try {
      await api.post('/documents', fd);
      setShowUpload(false);
      setUploadTitle('');
      setUploadDesc('');
      setUploadFile(null);
      if (fileRef.current) fileRef.current.value = '';
      fetchData();
    } catch (e: any) {
      alert(e.response?.data?.detail || e.message || 'Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const openConfirm = (e: React.MouseEvent, id: string, title: string) => {
    e.stopPropagation();
    e.preventDefault();
    setDeleteError('');
    setConfirmDoc({ id, title });
  };

  const confirmDelete = async () => {
    if (!confirmDoc) return;
    setDeleting(true);
    setDeleteError('');
    try {
      await api.delete(`/documents/${confirmDoc.id}`);
      setDocuments(prev => prev.filter(d => d.id !== confirmDoc.id));
      setConfirmDoc(null);
    } catch (e: any) {
      setDeleteError(e.response?.data?.detail || e.message || 'Delete failed.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-800">Document Management</h1>
          <p className="text-slate-500 mt-1">Upload and manage SOP documents</p>
        </div>
        <button
          type="button"
          onClick={() => setShowUpload(true)}
          className="bg-pharmacy-600 hover:bg-pharmacy-700 text-white px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 shadow-md transition-colors"
        >
          <Plus className="w-4 h-4" /> Upload
        </button>
      </header>

      {/* ── Upload Modal ──────────────────────────────────────────────────────── */}
      {showUpload && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
            <h2 className="text-xl font-bold mb-6 text-slate-800">Upload Document</h2>
            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-1 text-slate-600">Title</label>
                <input
                  type="text"
                  required
                  value={uploadTitle}
                  onChange={e => setUploadTitle(e.target.value)}
                  className="w-full px-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1 text-slate-600">Description</label>
                <input
                  type="text"
                  value={uploadDesc}
                  onChange={e => setUploadDesc(e.target.value)}
                  className="w-full px-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1 text-slate-600">Section</label>
                <select
                  required
                  value={uploadSection}
                  onChange={e => setUploadSection(e.target.value)}
                  className="w-full px-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500"
                >
                  {sections.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1 text-slate-600">File</label>
                <input
                  type="file"
                  required
                  ref={fileRef}
                  onChange={e => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowUpload(false)}
                  className="flex-1 py-2 rounded-xl border-2 border-slate-200 font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="flex-1 py-2 rounded-xl bg-pharmacy-600 text-white font-medium flex items-center justify-center gap-2"
                >
                  {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Upload'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Delete Confirmation Modal ─────────────────────────────────────────── */}
      {confirmDoc && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-8 max-w-sm w-full shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-red-100 rounded-xl">
                <Trash2 className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-800">Delete Document</h2>
                <p className="text-sm text-slate-500">This action cannot be undone</p>
              </div>
            </div>
            <p className="text-slate-700 mb-2">Are you sure you want to delete:</p>
            <p className="font-semibold text-slate-800 bg-slate-50 border border-slate-200 px-4 py-2 rounded-lg mb-4 truncate">
              {confirmDoc.title}
            </p>
            {deleteError && (
              <p className="text-red-600 text-sm bg-red-50 border border-red-100 px-3 py-2 rounded-lg mb-4">
                {deleteError}
              </p>
            )}
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => { setConfirmDoc(null); setDeleteError(''); }}
                disabled={deleting}
                className="flex-1 py-2.5 rounded-xl border-2 border-slate-200 font-medium text-slate-600 hover:bg-slate-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmDelete}
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

      {/* ── Documents Table ───────────────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        {loading ? (
          <div className="p-8 flex justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-pharmacy-500" />
          </div>
        ) : (
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
              <tr>
                <th className="px-6 py-4 uppercase">Title</th>
                <th className="px-6 py-4 uppercase">Section</th>
                <th className="px-6 py-4 uppercase text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {documents.map(d => (
                <tr key={d.id} className="hover:bg-slate-50/50">
                  <td className="px-6 py-4 font-medium text-slate-800">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-blue-500 flex-shrink-0" />
                      {d.title}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="bg-teal-50 text-teal-700 px-2 py-1 rounded font-semibold text-xs">
                      {d.section_name}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      type="button"
                      onClick={e => openConfirm(e, d.id, d.title)}
                      className="text-red-500 hover:text-red-700 hover:bg-red-50 p-2 rounded-lg transition-colors"
                      title="Delete document"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
