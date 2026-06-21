import React, { useState } from 'react';
import { AnimatedCard } from '../components/AnimatedCard';
import { Search, Package, MapPin, Layers, Scan, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const Warehouse: React.FC = () => {
  const [search, setSearch] = useState('');
  const [searchedItem, setSearchedItem] = useState<any>(null);
  const [isSearching, setIsSearching] = useState(false);

  // Mock data
  const inventory = {
    'BG-000123': {
      id: 'BG-000123',
      name: 'Sterile Glass Vials (50ml)',
      category: 'Packaging',
      quantity: 12500,
      unit: 'pcs',
      status: 'In Stock',
      location: {
        warehouse: 'Main Facility',
        zone: 'Zone B (Sterile)',
        rack: 'R-12',
        shelf: 'S-04',
        position: 'P-02'
      },
      lastUpdated: '2 hours ago'
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!search.trim()) return;
    
    setIsSearching(true);
    setSearchedItem(null);
    
    // Simulate API call
    setTimeout(() => {
      const item = inventory[search.toUpperCase() as keyof typeof inventory];
      setSearchedItem(item || 'NOT_FOUND');
      setIsSearching(false);
    }, 800);
  };

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-bold text-slate-800">Smart Inventory Tracker</h1>
        <p className="text-slate-500 mt-2">Real-time material location and status</p>
      </header>

      <AnimatedCard className="max-w-3xl mx-auto !p-8">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-pharmacy-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <Scan className="w-8 h-8 text-pharmacy-600" />
          </div>
          <h2 className="text-2xl font-bold text-slate-800">Scan or Enter Item Code</h2>
          <p className="text-slate-500">e.g. BG-000123</p>
        </div>

        <form onSubmit={handleSearch} className="relative max-w-xl mx-auto">
          <input 
            type="text" 
            placeholder="Enter material code..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-6 pr-16 py-4 text-lg bg-slate-50 border-2 border-slate-200 rounded-2xl focus:bg-white focus:ring-4 focus:ring-pharmacy-500/20 focus:border-pharmacy-500 outline-none transition-all uppercase tracking-wider font-mono shadow-inner"
          />
          <button 
            type="submit"
            disabled={isSearching}
            className="absolute right-2 top-2 bottom-2 bg-pharmacy-600 hover:bg-pharmacy-700 text-white p-3 rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center min-w-[56px]"
          >
            {isSearching ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            ) : (
              <Search className="w-5 h-5" />
            )}
          </button>
        </form>
      </AnimatedCard>

      <AnimatePresence mode="wait">
        {searchedItem && searchedItem !== 'NOT_FOUND' && (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="max-w-4xl mx-auto"
          >
            <AnimatedCard className="overflow-hidden !p-0 border-2 border-pharmacy-100">
              <div className="bg-gradient-to-r from-pharmacy-50 to-white p-6 md:p-8 border-b border-pharmacy-100 flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="flex items-center gap-6">
                  <div className="w-16 h-16 bg-white shadow-sm rounded-2xl flex items-center justify-center border border-slate-100 shrink-0">
                    <Package className="w-8 h-8 text-pharmacy-600" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-slate-800">{searchedItem.name}</h2>
                    <div className="flex items-center gap-3 mt-2">
                      <span className="font-mono bg-white px-3 py-1 rounded-md border border-slate-200 text-slate-600 font-medium">
                        {searchedItem.id}
                      </span>
                      <span className="text-sm px-3 py-1 rounded-full bg-green-100 text-green-700 font-bold">
                        {searchedItem.status}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white px-6 py-4 rounded-2xl shadow-sm border border-slate-100 text-center shrink-0">
                  <p className="text-sm text-slate-500 font-medium mb-1">Available Quantity</p>
                  <p className="text-3xl font-bold text-slate-800">
                    {searchedItem.quantity.toLocaleString()} <span className="text-lg text-slate-400 font-normal">{searchedItem.unit}</span>
                  </p>
                </div>
              </div>

              <div className="p-6 md:p-8 bg-slate-50">
                <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-pharmacy-600" />
                  Current Location Pathway
                </h3>
                
                <div className="flex flex-col md:flex-row items-center justify-between gap-4 relative">
                  {/* Decorative line connecting nodes on desktop */}
                  <div className="hidden md:block absolute top-1/2 left-0 right-0 h-1 bg-slate-200 -translate-y-1/2 z-0"></div>
                  
                  {[
                    { label: 'Facility', value: searchedItem.location.warehouse, icon: Layers },
                    { label: 'Zone', value: searchedItem.location.zone, icon: MapPin },
                    { label: 'Rack', value: searchedItem.location.rack, icon: Layers },
                    { label: 'Shelf', value: searchedItem.location.shelf, icon: Package },
                  ].map((loc, i) => (
                    <motion.div 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.2 + (i * 0.1) }}
                      key={loc.label} 
                      className="relative z-10 flex flex-col items-center gap-3 w-full md:w-auto"
                    >
                      <div className="w-14 h-14 rounded-xl bg-white shadow-md border border-slate-100 flex items-center justify-center text-slate-600 relative group hover:border-pharmacy-300 transition-colors">
                        <loc.icon className="w-6 h-6" />
                        {i < 3 && <ArrowRight className="md:hidden absolute -bottom-6 text-slate-300 w-4 h-4" />}
                      </div>
                      <div className="text-center bg-white px-4 py-2 rounded-lg shadow-sm border border-slate-100 w-full min-w-[120px]">
                        <p className="text-xs text-slate-400 uppercase font-bold tracking-wider mb-1">{loc.label}</p>
                        <p className="font-semibold text-slate-800">{loc.value}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </AnimatedCard>
          </motion.div>
        )}

        {searchedItem === 'NOT_FOUND' && (
          <motion.div
            key="not-found"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="max-w-2xl mx-auto text-center py-12"
          >
            <div className="w-20 h-20 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <Package className="w-8 h-8 text-red-400" />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">Item Not Found</h3>
            <p className="text-slate-500">The material code you entered does not exist in the current inventory system.</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
