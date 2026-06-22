import React, { useEffect, useState } from 'react';
import { Package, MapPin, Loader2, Search, Plus, X, Check, AlertCircle } from 'lucide-react';
import api from '../services/api';

export const AdminWarehouse: React.FC = () => {
  const [items, setItems] = useState<any[]>([]);
  const [locations, setLocations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  // Modals state
  const [showItemModal, setShowItemModal] = useState(false);
  const [showLocationModal, setShowLocationModal] = useState(false);

  // Item form state
  const [itemCode, setItemCode] = useState('');
  const [materialName, setMaterialName] = useState('');
  const [quantity, setQuantity] = useState('');
  const [unit, setUnit] = useState('KG');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [itemLoading, setItemLoading] = useState(false);
  const [itemError, setItemError] = useState('');
  const [isNewLocation, setIsNewLocation] = useState(false);

  // Location form state
  const [warehouseName, setWarehouseName] = useState('');
  const [rack, setRack] = useState('');
  const [shelf, setShelf] = useState('');
  const [position, setPosition] = useState('');
  const [locationLoading, setLocationLoading] = useState(false);
  const [locationError, setLocationError] = useState('');

  // Toast
  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 3500);
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const [itemsRes, locsRes] = await Promise.all([
        api.get('/warehouse/items'),
        api.get('/warehouse/locations')
      ]);
      setItems(itemsRes.data?.data || []);
      const loadedLocs = locsRes.data?.data || [];
      setLocations(loadedLocs);
      if (loadedLocs.length > 0 && !selectedLocation) {
        setSelectedLocation(loadedLocs[0].id);
      }
    } catch (e) {
      showToast('error', 'Failed to fetch warehouse data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filtered = items.filter((i: any) => 
    i.item_code.toLowerCase().includes(search.toLowerCase()) || 
    (i.material_name && i.material_name.toLowerCase().includes(search.toLowerCase())) ||
    (i.location?.location_code && i.location.location_code.toLowerCase().includes(search.toLowerCase()))
  );

  const handleCreateItem = async (e: React.FormEvent) => {
    e.preventDefault();
    setItemError('');
    setItemLoading(true);
    try {
      if (isNewLocation) {
        // Single transaction: create location + item together
        await api.post('/warehouse/items/with-location', {
          item_code: itemCode.trim().toUpperCase(),
          material_name: materialName.trim(),
          quantity: parseFloat(quantity),
          unit: unit.trim(),
          warehouse_name: warehouseName.trim(),
          rack: rack.trim().toUpperCase(),
          shelf: shelf.trim().toUpperCase(),
          position: position.trim().toUpperCase()
        });
      } else {
        await api.post('/warehouse/items', {
          item_code: itemCode.trim().toUpperCase(),
          material_name: materialName.trim(),
          quantity: parseFloat(quantity),
          unit: unit.trim(),
          location_id: selectedLocation
        });
      }
      showToast('success', `Item ${itemCode.toUpperCase()} added successfully.`);
      setShowItemModal(false);
      setItemCode('');
      setMaterialName('');
      setQuantity('');
      if (isNewLocation) {
         setWarehouseName('');
         setRack('');
         setShelf('');
         setPosition('');
         setIsNewLocation(false);
      }
      fetchData();
    } catch (e: any) {
      setItemError(e.response?.data?.detail || e.message || 'Failed to add item.');
    } finally {
      setItemLoading(false);
    }
  };

  const handleCreateLocation = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocationError('');
    setLocationLoading(true);
    try {
      await api.post('/warehouse/locations', {
        warehouse_name: warehouseName.trim(),
        rack: rack.trim().toUpperCase(),
        shelf: shelf.trim().toUpperCase(),
        position: position.trim().toUpperCase()
      });
      showToast('success', 'Location added successfully.');
      setShowLocationModal(false);
      setWarehouseName('');
      setRack('');
      setShelf('');
      setPosition('');
      fetchData();
    } catch (e: any) {
      setLocationError(e.response?.data?.detail || e.message || 'Failed to add location.');
    } finally {
      setLocationLoading(false);
    }
  };

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

      <header className="flex justify-between items-center flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-800 flex items-center gap-3">
             <span className="p-2 bg-pharmacy-100 text-pharmacy-600 rounded-xl">
               <Package className="w-6 h-6" />
             </span>
             Warehouse View
          </h1>
          <p className="text-slate-500 mt-1">Browse all inventory items and locations</p>
        </div>
        <div className="flex gap-3">
           <button 
             onClick={() => setShowLocationModal(true)}
             className="bg-white border-2 border-slate-200 text-slate-700 hover:border-pharmacy-400 hover:text-pharmacy-600 px-4 py-2.5 rounded-xl font-medium flex items-center gap-2 transition-colors"
           >
             <MapPin className="w-4 h-4" /> Add Location
           </button>
           <button 
             onClick={() => setShowItemModal(true)}
             className="bg-pharmacy-600 hover:bg-pharmacy-700 text-white px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 shadow-md transition-colors"
           >
             <Plus className="w-4 h-4" /> Add Item
           </button>
        </div>
      </header>

      <div className="relative max-w-md">
        <Search className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
        <input 
          type="text" 
          placeholder="Search by code, material, or location..." 
          value={search} 
          onChange={e => setSearch(e.target.value)}
          className="w-full pl-12 pr-4 py-3 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500 transition-colors" 
        />
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        {loading ? <div className="p-8 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-pharmacy-500" /></div> :
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left min-w-[600px]">
              <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-6 py-4 uppercase whitespace-nowrap">Item Code</th>
                  <th className="px-6 py-4 uppercase whitespace-nowrap">Material</th>
                  <th className="px-6 py-4 uppercase whitespace-nowrap">Quantity</th>
                  <th className="px-6 py-4 uppercase whitespace-nowrap">Location</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {filtered.map((i: any) => (
                  <tr key={i.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-4 whitespace-nowrap"><span className="font-mono bg-pharmacy-50 text-pharmacy-700 px-2 py-1 rounded font-semibold text-xs border border-pharmacy-100 shadow-sm">{i.item_code}</span></td>
                    <td className="px-6 py-4 font-medium text-slate-700 whitespace-nowrap">{i.material_name || '—'}</td>
                    <td className="px-6 py-4 whitespace-nowrap"><span className="font-bold text-slate-800">{i.quantity}</span> <span className="text-slate-400 text-xs">{i.unit || 'units'}</span></td>
                    <td className="px-6 py-4 flex items-center gap-2 text-slate-600 font-mono text-xs whitespace-nowrap"><MapPin className="w-4 h-4 text-slate-400 flex-shrink-0" /> {i.location?.location_code || '—'}</td>
                  </tr>
                ))}
                {filtered.length === 0 && <tr><td colSpan={4} className="p-12 text-center text-slate-500">No items found matching your search.</td></tr>}
              </tbody>
            </table>
          </div>
        }
      </div>

      {/* ── Add Item Modal ─────────────────────────────────────────────────── */}
      {showItemModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-xl font-bold text-slate-800">Add New Item</h2>
                <p className="text-sm text-slate-500 mt-0.5">Register a new item in the warehouse</p>
              </div>
              <button onClick={() => { setShowItemModal(false); setItemError(''); }} className="p-2 rounded-xl hover:bg-slate-100 text-slate-400">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateItem} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-1.5 text-slate-700">Item Code <span className="text-red-500">*</span></label>
                <input type="text" required placeholder="e.g. BG-000123" pattern="^[A-Za-z]{2}-\d{6}$" title="Format: 2 letters + dash + 6 digits (e.g. BG-000123)" value={itemCode} onChange={e => setItemCode(e.target.value)} className="w-full px-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500 uppercase font-mono" />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1.5 text-slate-700">Material Name <span className="text-red-500">*</span></label>
                <input type="text" required value={materialName} onChange={e => setMaterialName(e.target.value)} className="w-full px-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500" />
              </div>
              <div className="flex gap-4">
                <div className="flex-1">
                   <label className="block text-sm font-semibold mb-1.5 text-slate-700">Quantity <span className="text-red-500">*</span></label>
                   <input type="number" required min="0" step="0.01" value={quantity} onChange={e => setQuantity(e.target.value)} className="w-full px-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500" />
                </div>
                <div className="w-1/3">
                   <label className="block text-sm font-semibold mb-1.5 text-slate-700">Unit</label>
                   <select required value={unit} onChange={e => setUnit(e.target.value)} className="w-full px-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500 bg-white">
                     <option value="KG">KG</option>
                     <option value="L">Liters (L)</option>
                     <option value="PCS">Pieces (PCS)</option>
                     <option value="units">Units</option>
                     <option value="boxes">Boxes</option>
                     <option value="pallets">Pallets</option>
                     <option value="packs">Packs</option>
                   </select>
                </div>
              </div>
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="block text-sm font-semibold text-slate-700">Initial Location <span className="text-red-500">*</span></label>
                  <button type="button" onClick={() => setIsNewLocation(!isNewLocation)} className="text-xs font-medium text-pharmacy-600 hover:text-pharmacy-700">
                    {isNewLocation ? 'Select Existing' : '+ Create New'}
                  </button>
                </div>
                
                {!isNewLocation ? (
                  locations.length === 0 ? (
                     <p className="text-sm text-amber-600 bg-amber-50 p-2 rounded-lg border border-amber-100 flex items-center gap-2"><AlertCircle className="w-4 h-4" /> Please add a location first or create one now.</p>
                  ) : (
                     <select required value={selectedLocation} onChange={e => setSelectedLocation(e.target.value)} className="w-full px-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500">
                       {locations.map(loc => <option key={loc.id} value={loc.id}>{loc.location_code}</option>)}
                     </select>
                  )
                ) : (
                  <div className="space-y-3 bg-slate-50 p-4 rounded-xl border border-slate-200">
                    <div>
                      <input type="text" required placeholder="Warehouse Name (e.g. Main)" value={warehouseName} onChange={e => setWarehouseName(e.target.value)} className="w-full px-3 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500 text-sm" />
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                       <input type="text" required placeholder="Rack (R01)" value={rack} onChange={e => setRack(e.target.value)} className="w-full px-3 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500 uppercase font-mono text-sm" />
                       <input type="text" required placeholder="Shelf (S01)" value={shelf} onChange={e => setShelf(e.target.value)} className="w-full px-3 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500 uppercase font-mono text-sm" />
                       <input type="text" required placeholder="Pos (P01)" value={position} onChange={e => setPosition(e.target.value)} className="w-full px-3 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500 uppercase font-mono text-sm" />
                    </div>
                  </div>
                )}
              </div>

              {itemError && <div className="text-red-600 text-sm bg-red-50 border border-red-100 px-4 py-3 rounded-xl flex items-center gap-2"><AlertCircle className="w-4 h-4 flex-shrink-0"/> {itemError}</div>}

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowItemModal(false)} className="flex-1 py-2.5 rounded-xl border-2 border-slate-200 font-medium text-slate-600 hover:bg-slate-50">Cancel</button>
                <button type="submit" disabled={itemLoading || (!isNewLocation && locations.length === 0)} className="flex-1 py-2.5 rounded-xl bg-pharmacy-600 text-white font-medium flex items-center justify-center gap-2 disabled:opacity-60">{itemLoading ? <Loader2 className="w-4 h-4 animate-spin"/> : <Plus className="w-4 h-4"/>} Add Item</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Add Location Modal ─────────────────────────────────────────────── */}
      {showLocationModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-xl font-bold text-slate-800">Add New Location</h2>
                <p className="text-sm text-slate-500 mt-0.5">Define a new physical space in the warehouse</p>
              </div>
              <button onClick={() => { setShowLocationModal(false); setLocationError(''); }} className="p-2 rounded-xl hover:bg-slate-100 text-slate-400">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateLocation} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-1.5 text-slate-700">Warehouse Name <span className="text-red-500">*</span></label>
                <input type="text" required placeholder="e.g. Main Warehouse" value={warehouseName} onChange={e => setWarehouseName(e.target.value)} className="w-full px-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500" />
              </div>
              
              <div className="grid grid-cols-3 gap-3">
                 <div>
                   <label className="block text-sm font-semibold mb-1.5 text-slate-700">Rack <span className="text-red-500">*</span></label>
                   <input type="text" required placeholder="e.g. R01" value={rack} onChange={e => setRack(e.target.value)} className="w-full px-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500 uppercase font-mono" />
                 </div>
                 <div>
                   <label className="block text-sm font-semibold mb-1.5 text-slate-700">Shelf <span className="text-red-500">*</span></label>
                   <input type="text" required placeholder="e.g. S01" value={shelf} onChange={e => setShelf(e.target.value)} className="w-full px-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500 uppercase font-mono" />
                 </div>
                 <div>
                   <label className="block text-sm font-semibold mb-1.5 text-slate-700">Position <span className="text-red-500">*</span></label>
                   <input type="text" required placeholder="e.g. P01" value={position} onChange={e => setPosition(e.target.value)} className="w-full px-4 py-2 border-2 border-slate-200 rounded-xl outline-none focus:border-pharmacy-500 uppercase font-mono" />
                 </div>
              </div>
              
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 mt-2">
                 <p className="text-xs text-slate-500 font-semibold uppercase mb-1">Generated Code</p>
                 <p className="font-mono font-bold text-slate-800 tracking-wider">
                   {warehouseName ? warehouseName.split(' ').map(w=>w[0]).join('').toUpperCase() : 'WH'}-{rack.toUpperCase() || 'RXX'}-{shelf.toUpperCase() || 'SXX'}-{position.toUpperCase() || 'PXX'}
                 </p>
              </div>

              {locationError && <div className="text-red-600 text-sm bg-red-50 border border-red-100 px-4 py-3 rounded-xl flex items-center gap-2"><AlertCircle className="w-4 h-4 flex-shrink-0"/> {locationError}</div>}

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowLocationModal(false)} className="flex-1 py-2.5 rounded-xl border-2 border-slate-200 font-medium text-slate-600 hover:bg-slate-50">Cancel</button>
                <button type="submit" disabled={locationLoading} className="flex-1 py-2.5 rounded-xl bg-pharmacy-600 text-white font-medium flex items-center justify-center gap-2 disabled:opacity-60">{locationLoading ? <Loader2 className="w-4 h-4 animate-spin"/> : <MapPin className="w-4 h-4"/>} Add Location</button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
