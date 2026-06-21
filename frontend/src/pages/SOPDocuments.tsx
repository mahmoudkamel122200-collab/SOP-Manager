import React, { useState } from 'react';
import { AnimatedCard } from '../components/AnimatedCard';
import { Search, Filter, FileText, Download, Eye } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const SOPDocuments: React.FC = () => {
  const [search, setSearch] = useState('');
  const [selectedSection, setSelectedSection] = useState('All');

  const sections = ['All', 'Production', 'Labs', 'Warehouse', 'Quality'];

  const documents = [
    { id: 1, title: 'Machine Cleaning SOP', version: '2.0', section: 'Production', date: '2023-10-15', status: 'Active' },
    { id: 2, title: 'Sterilization Protocol', version: '1.4', section: 'Labs', date: '2023-09-22', status: 'Active' },
    { id: 3, title: 'Material Handling Guidelines', version: '3.1', section: 'Warehouse', date: '2023-11-05', status: 'Active' },
    { id: 4, title: 'Quality Assurance Testing', version: '2.2', section: 'Quality', date: '2023-10-30', status: 'Review' },
    { id: 5, title: 'Gowning Procedure', version: '1.0', section: 'Production', date: '2023-08-14', status: 'Active' },
  ];

  const filteredDocs = documents.filter(doc => {
    const matchesSearch = doc.title.toLowerCase().includes(search.toLowerCase());
    const matchesSection = selectedSection === 'All' || doc.section === selectedSection;
    return matchesSearch && matchesSection;
  });

  return (
    <div className="space-y-8">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">SOP Library</h1>
          <p className="text-slate-500 mt-2">Digital pharmaceutical document management</p>
        </div>
      </header>

      <AnimatedCard className="flex flex-col md:flex-row gap-4 items-center !p-4">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
          <input 
            type="text" 
            placeholder="Search documents by title or keywords..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-12 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-pharmacy-500 focus:border-transparent outline-none transition-all"
          />
        </div>
        <div className="flex gap-2 w-full md:w-auto overflow-x-auto pb-2 md:pb-0 hide-scrollbar">
          {sections.map(section => (
            <button
              key={section}
              onClick={() => setSelectedSection(section)}
              className={`whitespace-nowrap px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedSection === section 
                  ? 'bg-pharmacy-100 text-pharmacy-700' 
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
              }`}
            >
              {section}
            </button>
          ))}
        </div>
      </AnimatedCard>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <AnimatePresence>
          {filteredDocs.map((doc, index) => (
            <motion.div
              key={doc.id}
              layout
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.2, delay: index * 0.05 }}
            >
              <AnimatedCard className="h-full flex flex-col group">
                <div className="flex justify-between items-start mb-4">
                  <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
                    <FileText className="w-5 h-5" />
                  </div>
                  <span className={`px-2 py-1 text-xs font-bold rounded-md ${
                    doc.status === 'Active' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                  }`}>
                    {doc.status}
                  </span>
                </div>
                
                <h3 className="text-lg font-bold text-slate-800 mb-1 line-clamp-2" title={doc.title}>
                  {doc.title}
                </h3>
                
                <div className="flex items-center gap-2 mb-6">
                  <span className="text-xs font-semibold bg-slate-100 text-slate-600 px-2 py-1 rounded">v{doc.version}</span>
                  <span className="text-xs text-slate-500">{doc.section}</span>
                </div>
                
                <div className="mt-auto pt-4 border-t border-slate-100 flex justify-between items-center">
                  <span className="text-xs text-slate-400">Updated: {doc.date}</span>
                  <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-2 text-slate-400 hover:text-pharmacy-600 hover:bg-pharmacy-50 rounded-lg transition-colors" title="View Document">
                      <Eye className="w-4 h-4" />
                    </button>
                    <button className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Download PDF">
                      <Download className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </AnimatedCard>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {filteredDocs.length === 0 && (
        <motion.div 
          initial={{ opacity: 0 }} 
          animate={{ opacity: 1 }} 
          className="text-center py-20"
        >
          <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <Filter className="w-8 h-8 text-slate-400" />
          </div>
          <h3 className="text-xl font-bold text-slate-800 mb-2">No documents found</h3>
          <p className="text-slate-500">Try adjusting your search or filter criteria.</p>
        </motion.div>
      )}
    </div>
  );
};
