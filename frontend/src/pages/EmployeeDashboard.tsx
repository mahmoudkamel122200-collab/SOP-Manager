import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText, ExternalLink, Search, MapPin, ArrowRightLeft,
  Loader2, CheckCircle, XCircle, Printer
} from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

export const EmployeeDashboard: React.FC = () => {
  const { user, section } = useAuth();

  // --- SOP Documents ---
  const [documents, setDocuments] = useState<any[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);

  // --- Warehouse Search ---
  const [itemCode, setItemCode] = useState('');
  const [searchResult, setSearchResult] = useState<any | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState('');

  // --- Move Item ---
  const [moveItemCode, setMoveItemCode] = useState('');
  const [moveLocationCode, setMoveLocationCode] = useState('');
  const [moveLoading, setMoveLoading] = useState(false);
  const [moveMessage, setMoveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (section?.id) {
      setDocsLoading(true);
      api.get(`/documents/section/${section.id}`)
        .then(res => setDocuments(res.data?.data?.documents ?? []))
        .catch(() => setDocuments([]))
        .finally(() => setDocsLoading(false));
    }
  }, [section]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!itemCode.trim()) return;
    setSearchLoading(true);
    setSearchError('');
    setSearchResult(null);

    try {
      const res = await api.get(`/warehouse/items/${itemCode.trim().toUpperCase()}`);
      setSearchResult(res.data?.data);
    } catch (err: any) {
      setSearchError(err.response?.data?.detail || 'Item not found');
    } finally {
      setSearchLoading(false);
    }
  };

  const handleMove = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!moveItemCode.trim() || !moveLocationCode.trim()) return;
    setMoveLoading(true);
    setMoveMessage(null);

    try {
      // Search item by code — the response includes the UUID directly.
      const searchRes = await api.get(`/warehouse/items/${moveItemCode.trim().toUpperCase()}`);
      const itemData = searchRes.data?.data;

      const itemId = itemData?.id;
      if (!itemId) {
        throw new Error('Item not found or ID missing from response.');
      }

      // Also we need location_id, but the user inputs location_code. We need to fetch locations.
      const locRes = await api.get('/warehouse/locations');
      const foundLoc = (locRes.data?.data || []).find((l: any) => l.location_code === moveLocationCode.trim().toUpperCase());
      
      if (!foundLoc) {
         throw new Error(`Location ${moveLocationCode} not found.`);
      }

      await api.post(`/warehouse/items/${itemId}/move`, {
        new_location_id: foundLoc.id,
        notes: 'Employee move'
      });

      setMoveMessage({ type: 'success', text: `Moved ${itemData.item_code} to ${foundLoc.location_code}` });
      setMoveItemCode('');
      setMoveLocationCode('');
    } catch (err: any) {
      setMoveMessage({ type: 'error', text: err.response?.data?.detail || err.message || 'Move failed.' });
    } finally {
      setMoveLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-extrabold text-slate-800">
          Welcome, <span className="text-gradient">{user?.username}</span>
        </h1>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* SOP Documents */}
        <div className="lg:col-span-1 bg-white rounded-2xl shadow-sm border border-slate-100 flex flex-col overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center gap-3 bg-slate-50/50">
            <div className="p-2 bg-blue-100 text-blue-600 rounded-lg">
              <FileText className="w-5 h-5" />
            </div>
            <h2 className="font-bold text-slate-800 text-lg">SOP Documents</h2>
          </div>
          <div className="p-5 flex-1 overflow-y-auto">
            {docsLoading ? (
               <div className="flex justify-center"><Loader2 className="animate-spin text-blue-500 w-6 h-6" /></div>
            ) : documents.length === 0 ? (
               <p className="text-slate-500 text-center text-sm">No documents found.</p>
            ) : (
              <ul className="space-y-3">
                {documents.map(doc => (
                  <li key={doc.id} className="flex justify-between items-center p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <div>
                      <p className="font-semibold text-slate-700 text-sm">{doc.title}</p>
                      <p className="text-xs text-slate-500 mt-0.5">v{doc.version_number}</p>
                    </div>
                    <div className="flex gap-2">
                      <button 
                        onClick={async () => {
                          try {
                            const res = await api.get(`/documents/${doc.id}`);
                            const downloadUrl = res.data?.data?.download_url;
                            if (downloadUrl) {
                              window.open(downloadUrl, '_blank');
                            } else {
                              throw new Error('No download URL');
                            }
                          } catch(e) {
                            alert('Failed to open document');
                          }
                        }}
                        className="text-xs bg-white border border-slate-200 hover:border-blue-300 hover:text-blue-600 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 font-medium shadow-sm"
                      >
                        View <ExternalLink className="w-3 h-3" />
                      </button>
                      <button 
                        onClick={async () => {
                          try {
                            const res = await api.get(`/documents/${doc.id}`);
                            const downloadUrl = res.data?.data?.download_url;
                            if (!downloadUrl) throw new Error('No download URL');

                            // Fetch the file directly without Auth header to avoid CORS issues
                            const fileRes = await fetch(downloadUrl);
                            const blob = await fileRes.blob();
                            const url = window.URL.createObjectURL(blob);
                            
                            const iframe = document.createElement('iframe');
                            iframe.style.display = 'none';
                            iframe.src = url;
                            document.body.appendChild(iframe);
                            iframe.onload = () => {
                              iframe.contentWindow?.focus();
                              iframe.contentWindow?.print();
                            };
                          } catch(e) {
                            alert('Failed to print document');
                          }
                        }}
                        className="text-xs bg-white border border-slate-200 hover:border-teal-300 hover:text-teal-600 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 font-medium shadow-sm"
                      >
                        Print <Printer className="w-3 h-3" />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Warehouse */}
        <div className="lg:col-span-2 space-y-6">
          {/* Search */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-pharmacy-100 text-pharmacy-600 rounded-lg">
                <Search className="w-5 h-5" />
              </div>
              <h2 className="font-bold text-slate-800 text-lg">Warehouse Search</h2>
            </div>
            <form onSubmit={handleSearch} className="flex gap-3">
              <input 
                type="text" 
                placeholder="Item Code (e.g. BG-000123)"
                value={itemCode}
                onChange={e => setItemCode(e.target.value)}
                className="flex-1 px-4 py-2 border-2 border-slate-200 rounded-xl focus:border-pharmacy-500 outline-none uppercase font-mono bg-slate-50 focus:bg-white"
                required
              />
              <button disabled={searchLoading} className="bg-pharmacy-600 hover:bg-pharmacy-700 text-white px-6 rounded-xl font-medium transition-colors flex items-center gap-2 shadow-sm">
                {searchLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />} Search
              </button>
            </form>

            <AnimatePresence>
              {searchError && <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-sm mt-3">{searchError}</motion.p>}
              {searchResult && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-4 bg-pharmacy-50 border border-pharmacy-100 rounded-xl p-4">
                  <div className="flex justify-between items-center mb-3 pb-3 border-b border-pharmacy-200/50">
                    <div>
                      <p className="font-bold text-slate-800 text-lg">{searchResult.material}</p>
                      <p className="font-mono text-xs text-pharmacy-700">{searchResult.item_code}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-2xl text-slate-800">{searchResult.quantity}</p>
                      <p className="text-xs text-slate-500">units</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1"><MapPin className="w-3 h-3" /> Location</p>
                    <div className="grid grid-cols-4 gap-2">
                      {['warehouse', 'rack', 'shelf', 'position'].map(key => (
                         <div key={key} className="bg-white rounded-lg p-2 border border-slate-100 text-center">
                           <p className="text-[10px] text-slate-400 uppercase">{key}</p>
                           <p className="font-semibold text-slate-700 text-sm">{searchResult.location?.[key] || '—'}</p>
                         </div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Move */}
          {(section?.permission_level === 'WRITE' || section?.permission_level === 'ADMIN' || user?.role === 'ADMIN') && (
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-purple-100 text-purple-600 rounded-lg">
                  <ArrowRightLeft className="w-5 h-5" />
                </div>
                <h2 className="font-bold text-slate-800 text-lg">Move Item</h2>
              </div>
              <form onSubmit={handleMove} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                 <div>
                   <label className="block text-sm font-medium text-slate-600 mb-1">Item Code</label>
                   <input type="text" value={moveItemCode} onChange={e => setMoveItemCode(e.target.value)} placeholder="BG-000123" className="w-full px-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-purple-500 uppercase font-mono bg-slate-50 focus:bg-white" required />
                 </div>
                 <div>
                   <label className="block text-sm font-medium text-slate-600 mb-1">New Location Code</label>
                   <input type="text" value={moveLocationCode} onChange={e => setMoveLocationCode(e.target.value)} placeholder="A-R02-S01-P02" className="w-full px-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-purple-500 uppercase font-mono bg-slate-50 focus:bg-white" required />
                 </div>
                 <div className="md:col-span-2">
                   <button disabled={moveLoading} className="w-full bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-xl font-semibold transition-colors flex justify-center items-center gap-2 shadow-md disabled:opacity-60">
                     {moveLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRightLeft className="w-4 h-4" />} Move Item
                   </button>
                 </div>
              </form>
              {moveMessage && (
                 <div className={`mt-4 p-3 rounded-xl flex items-center gap-2 text-sm font-medium ${moveMessage.type === 'success' ? 'bg-green-50 text-green-700 border border-green-100' : 'bg-red-50 text-red-600 border border-red-100'}`}>
                   {moveMessage.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                   {moveMessage.text}
                 </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
