import React, { useState, useEffect, useRef } from 'react';
import { FileText, Trash2, Loader2, Plus, X, UploadCloud } from 'lucide-react';
import api from '../services/api';

export const AdminDocuments: React.FC = () => {
  const [documents, setDocuments] = useState<any[]>([]);
  const [sections, setSections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Upload Form
  const [showUpload, setShowUpload] = useState(false);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadDesc, setUploadDesc] = useState('');
  const [uploadSections, setUploadSections] = useState<string[]>([]);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  // Edit Modal
  const [editDoc, setEditDoc] = useState<any | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editSections, setEditSections] = useState<string[]>([]);
  const [editing, setEditing] = useState(false);

  // Delete confirm modal
  const [confirmDoc, setConfirmDoc] = useState<{ id: string; title: string } | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState('');

  const openEdit = (e: React.MouseEvent, doc: any) => {
    e.stopPropagation();
    setEditDoc(doc);
    setEditTitle(doc.title);
    setEditSections(doc.sections?.map((s: any) => s.id) || (sections[0] ? [sections[0].id] : []));
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editDoc) return;
    setEditing(true);
    try {
      await api.patch(`/documents/${editDoc.id}`, {
        title: editTitle,
        section_ids: editSections
      });
      setEditDoc(null);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message || 'Edit failed.');
    } finally {
      setEditing(false);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const secRes = await api.get('/sections');
      const secs = secRes.data?.data || [];
      setSections(secs);
      if (secs.length > 0) setUploadSections([secs[0].id]);

      const dRes = await api.get('/documents?page_size=100');
      const docs = dRes.data?.data?.documents || [];
      setDocuments(docs);
    } catch (e) {
      console.error(e);
    }
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
    fd.append('section_ids', uploadSections.join(','));
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
      alert(e.response?.data?.message || e.response?.data?.detail || e.message || 'Upload failed.');
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

      {/* ── Edit Modal ──────────────────────────────────────────────────────── */}
      {editDoc && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
            <h2 className="text-xl font-bold mb-6 text-slate-800">Edit Document</h2>
            <form onSubmit={handleEdit} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-1 text-slate-600">Title</label>
                <input
                  type="text"
                  required
                  value={editTitle}
                  onChange={e => setEditTitle(e.target.value)}
                  className="w-full px-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1 text-slate-600">Sections</label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {editSections.map(id => {
                    const sec = sections.find(s => s.id === id);
                    if (!sec) return null;
                    return (
                      <div key={id} className="bg-pharmacy-100 text-pharmacy-700 px-3 py-1 rounded-lg text-sm flex items-center gap-2">
                        {sec.name}
                        <button type="button" onClick={() => setEditSections(editSections.filter(i => i !== id))} className="text-pharmacy-500 hover:text-pharmacy-800"><X className="w-3 h-3" /></button>
                      </div>
                    );
                  })}
                </div>
                <select
                  value=""
                  onChange={(e) => {
                    if (e.target.value && !editSections.includes(e.target.value)) {
                      setEditSections([...editSections, e.target.value]);
                    }
                  }}
                  className="w-full px-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500"
                >
                  <option value="">Add a section...</option>
                  {sections.filter(s => !editSections.includes(s.id)).map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setEditDoc(null)}
                  className="flex-1 py-2 rounded-xl border-2 border-slate-200 font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editing}
                  className="flex-1 py-2 rounded-xl bg-pharmacy-600 text-white font-medium flex items-center justify-center gap-2"
                >
                  {editing ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

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
                <label className="block text-sm font-semibold mb-1 text-slate-600">Sections</label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {uploadSections.map(id => {
                    const sec = sections.find(s => s.id === id);
                    if (!sec) return null;
                    return (
                      <div key={id} className="bg-pharmacy-100 text-pharmacy-700 px-3 py-1 rounded-lg text-sm flex items-center gap-2">
                        {sec.name}
                        <button type="button" onClick={() => setUploadSections(uploadSections.filter(i => i !== id))} className="text-pharmacy-500 hover:text-pharmacy-800"><X className="w-3 h-3" /></button>
                      </div>
                    );
                  })}
                </div>
                <select
                  value=""
                  onChange={(e) => {
                    if (e.target.value && !uploadSections.includes(e.target.value)) {
                      setUploadSections([...uploadSections, e.target.value]);
                    }
                  }}
                  className="w-full px-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500"
                >
                  <option value="">Add a section...</option>
                  {sections.filter(s => !uploadSections.includes(s.id)).map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1 text-slate-600">File</label>
                <div
                  onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
                  onDragLeave={(e) => { e.preventDefault(); setIsDragOver(false); }}
                  onDrop={(e) => {
                    e.preventDefault();
                    setIsDragOver(false);
                    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                      setUploadFile(e.dataTransfer.files[0]);
                    }
                  }}
                  className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${
                    isDragOver ? 'border-pharmacy-500 bg-pharmacy-50' : 'border-slate-300 hover:bg-slate-50'
                  }`}
                  onClick={() => fileRef.current?.click()}
                >
                  <UploadCloud className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  {uploadFile ? (
                    <p className="text-sm font-medium text-pharmacy-600">{uploadFile.name}</p>
                  ) : (
                    <p className="text-sm text-slate-500">Drag & drop a file here, or click to select</p>
                  )}
                  <input
                    type="file"
                    ref={fileRef}
                    className="hidden"
                    onChange={e => setUploadFile(e.target.files?.[0] || null)}
                  />
                </div>
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
                    <div className="flex flex-wrap gap-1">
                      {d.sections?.map((sec: any) => (
                        <span key={sec.id} className="bg-teal-50 text-teal-700 px-2 py-1 rounded font-semibold text-xs">
                          {sec.name}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={e => openEdit(e, d)}
                      className="text-blue-500 hover:text-blue-700 hover:bg-blue-50 p-2 rounded-lg transition-colors"
                      title="Edit document"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
                    </button>
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
