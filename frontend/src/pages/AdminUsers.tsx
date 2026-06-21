import React, { useState, useEffect } from 'react';
import {
  Users, Plus, Trash2, Loader2, ShieldAlert,
  Check, AlertCircle, X, UserPlus, Key, Mail, Shield, Building, Lock
} from 'lucide-react';
import api from '../services/api';

interface Role {
  id: string;
  name: string;
  description: string;
}

interface UserOut {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
  role: Role;
}

interface Section {
  id: string;
  name: string;
}

interface UserSection {
  id: string;
  section_name: string;
  permission_level: string;
}

export const AdminUsers: React.FC = () => {
  const [users, setUsers] = useState<UserOut[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [showCreate, setShowCreate] = useState(false);
  const [showAssign, setShowAssign] = useState<UserOut | null>(null);

  // Form State - Create User
  const [formData, setFormData] = useState({
    username: '', email: '', password: '', full_name: '', role_id: '',
    section_id: '', permission_level: 'READ'
  });
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');

  // Form State - Assign Section
  const [assignData, setAssignData] = useState({ section_id: '', permission_level: 'READ' });
  const [assigning, setAssigning] = useState(false);
  const [assignError, setAssignError] = useState('');
  
  // User Sections List
  const [userSections, setUserSections] = useState<UserSection[]>([]);
  const [loadingSections, setLoadingSections] = useState(false);

  // Toast
  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 3500);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [uRes, rRes, sRes] = await Promise.all([
        api.get('/users?page_size=100'),
        api.get('/users/roles'),
        api.get('/sections')
      ]);
      setUsers(uRes.data?.data || []);
      setRoles(rRes.data?.data || []);
      setSections(sRes.data?.data || []);
      
      if (rRes.data?.data?.length > 0) {
        setFormData(prev => ({ ...prev, role_id: rRes.data.data[0].id }));
      }
    } catch (e) {
      showToast('error', 'Failed to load users data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setCreateError('');
    try {
      const payload = {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name || null,
        role_id: formData.role_id
      };
      
      // Create user
      const userRes = await api.post('/users', payload);
      const newUser = userRes.data.data;
      
      // Assign section if selected
      if (formData.section_id) {
        await api.post('/sections/assign', {
          user_id: newUser.id,
          section_id: formData.section_id,
          permission_level: formData.permission_level
        });
      }

      setShowCreate(false);
      setFormData(prev => ({ ...prev, username: '', email: '', password: '', full_name: '', section_id: '', permission_level: 'READ' }));
      showToast('success', `User ${newUser.username} created successfully.`);
      loadData();
    } catch (e: any) {
      setCreateError(e.response?.data?.message || e.response?.data?.detail || e.message || 'Create failed.');
    } finally {
      setCreating(false);
    }
  };

  const loadUserSections = async (userId: string) => {
    setLoadingSections(true);
    try {
      const res = await api.get(`/users/${userId}/sections`);
      setUserSections(res.data?.data || []);
    } catch {
      showToast('error', 'Failed to load user assignments');
    } finally {
      setLoadingSections(false);
    }
  };

  const openAssignModal = (user: UserOut) => {
    setShowAssign(user);
    setAssignData({ section_id: '', permission_level: 'READ' });
    setUserSections([]);
    loadUserSections(user.id);
  };

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showAssign || !assignData.section_id) return;
    setAssigning(true);
    setAssignError('');
    try {
      await api.post('/sections/assign', {
        user_id: showAssign.id,
        section_id: assignData.section_id,
        permission_level: assignData.permission_level
      });
      showToast('success', 'Section access granted successfully.');
      loadUserSections(showAssign.id);
      setAssignData({ section_id: '', permission_level: 'READ' });
    } catch (e: any) {
      setAssignError(e.response?.data?.message || e.response?.data?.detail || e.message || 'Failed to assign section.');
    } finally {
      setAssigning(false);
    }
  };

  const handleRevoke = async (assignmentId: string) => {
    if (!window.confirm('Are you sure you want to revoke this access?')) return;
    try {
      await api.delete(`/sections/assign/${assignmentId}`);
      showToast('success', 'Access revoked.');
      if (showAssign) loadUserSections(showAssign.id);
    } catch {
      showToast('error', 'Failed to revoke access.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-6 right-6 z-[100] flex items-center gap-3 px-5 py-4 rounded-2xl shadow-xl text-sm font-semibold transition-all
          ${toast.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}
        >
          {toast.type === 'success' ? <Check className="w-4 h-4 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 flex-shrink-0" />}
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-800 flex items-center gap-3">
            <span className="p-2 bg-blue-100 text-blue-600 rounded-xl">
              <Users className="w-6 h-6" />
            </span>
            Users Management
          </h1>
          <p className="text-slate-500 mt-1">Add users and configure section access permissions</p>
        </div>
        <button
          onClick={() => { setShowCreate(true); setCreateError(''); }}
          className="bg-pharmacy-600 hover:bg-pharmacy-700 text-white px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 shadow-md transition-colors"
        >
          <UserPlus className="w-4 h-4" /> New User
        </button>
      </header>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-[100] p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl p-8 max-w-2xl w-full shadow-2xl my-auto">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-xl font-bold text-slate-800">Create New User</h2>
                <p className="text-sm text-slate-500 mt-0.5">Register a new system user and set permissions</p>
              </div>
              <button onClick={() => setShowCreate(false)} className="p-2 rounded-xl hover:bg-slate-100 text-slate-400">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold mb-1.5 text-slate-700">Username *</label>
                  <input
                    type="text" required minLength={3}
                    value={formData.username} onChange={e => setFormData({ ...formData, username: e.target.value })}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl focus:border-pharmacy-500 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold mb-1.5 text-slate-700">Full Name</label>
                  <input
                    type="text"
                    value={formData.full_name} onChange={e => setFormData({ ...formData, full_name: e.target.value })}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl focus:border-pharmacy-500 transition-colors"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-semibold mb-1.5 text-slate-700">Email Address *</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type="email" required
                    value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })}
                    className="w-full pl-11 pr-4 py-2.5 border-2 border-slate-200 rounded-xl focus:border-pharmacy-500 transition-colors"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold mb-1.5 text-slate-700">Password *</label>
                  <div className="relative">
                    <Key className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <input
                      type="password" required minLength={8}
                      value={formData.password} onChange={e => setFormData({ ...formData, password: e.target.value })}
                      placeholder="Min 8 chars, 1 uppercase, 1 digit"
                      className="w-full pl-11 pr-4 py-2.5 border-2 border-slate-200 rounded-xl focus:border-pharmacy-500 transition-colors text-sm"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-semibold mb-1.5 text-slate-700">Role *</label>
                  <div className="relative">
                    <Shield className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
                    <select
                      value={formData.role_id} onChange={e => setFormData({ ...formData, role_id: e.target.value })}
                      className="w-full pl-11 pr-4 py-2.5 border-2 border-slate-200 rounded-xl focus:border-pharmacy-500 transition-colors bg-white appearance-none"
                      required
                    >
                      {roles.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
                    </select>
                  </div>
                </div>
              </div>

              {/* Initial Section Assignment */}
              <div className="pt-4 border-t border-slate-100 mt-4">
                <h3 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
                  <Building className="w-4 h-4 text-slate-400" /> Optional: Assign Initial Section
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <select
                    value={formData.section_id} onChange={e => setFormData({ ...formData, section_id: e.target.value })}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl focus:border-pharmacy-500 transition-colors bg-white"
                  >
                    <option value="">-- No Section --</option>
                    {sections.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                  
                  <select
                    value={formData.permission_level} onChange={e => setFormData({ ...formData, permission_level: e.target.value })}
                    disabled={!formData.section_id}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl focus:border-pharmacy-500 transition-colors bg-white disabled:bg-slate-50 disabled:text-slate-400"
                  >
                    <option value="READ">Read Only</option>
                    <option value="WRITE">Read & Write</option>
                    <option value="ADMIN">Section Admin</option>
                  </select>
                </div>
              </div>

              {createError && (
                <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-100 px-4 py-3 rounded-xl mt-4">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {createError}
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowCreate(false)} className="flex-1 py-2.5 rounded-xl border-2 border-slate-200 font-medium text-slate-600 hover:bg-slate-50">Cancel</button>
                <button type="submit" disabled={creating} className="flex-1 py-2.5 rounded-xl bg-pharmacy-600 hover:bg-pharmacy-700 text-white font-medium flex justify-center items-center gap-2 disabled:opacity-60">
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Assign Modal */}
      {showAssign && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
          <div className="bg-white rounded-2xl p-8 max-w-lg w-full shadow-2xl">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-xl font-bold text-slate-800">Manage Access</h2>
                <p className="text-sm text-slate-500 mt-0.5">Assign sections to <span className="font-semibold text-slate-700">{showAssign.username}</span></p>
              </div>
              <button onClick={() => setShowAssign(null)} className="p-2 rounded-xl hover:bg-slate-100 text-slate-400">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Current Assignments */}
            <div className="mb-6">
              <h3 className="text-sm font-bold text-slate-700 mb-3 uppercase tracking-wider">Current Access</h3>
              {loadingSections ? (
                <div className="py-4 flex justify-center"><Loader2 className="w-5 h-5 animate-spin text-slate-400" /></div>
              ) : userSections.length === 0 ? (
                <div className="py-4 bg-slate-50 rounded-xl border border-slate-200 border-dashed text-center text-sm text-slate-500">
                  No sections assigned to this user yet.
                </div>
              ) : (
                <div className="space-y-2">
                  {userSections.map(us => (
                    <div key={us.id} className="flex items-center justify-between p-3 bg-slate-50 border border-slate-100 rounded-xl">
                      <div>
                        <div className="font-medium text-slate-800">{us.section_name}</div>
                        <div className="text-xs text-slate-500 font-mono mt-0.5">{us.permission_level}</div>
                      </div>
                      <button onClick={() => handleRevoke(us.id)} className="p-2 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Revoke Access">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Grant New Access */}
            <form onSubmit={handleAssign} className="pt-5 border-t border-slate-100">
              <h3 className="text-sm font-bold text-slate-700 mb-3 uppercase tracking-wider">Grant New Access</h3>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <select
                  value={assignData.section_id} onChange={e => setAssignData({ ...assignData, section_id: e.target.value })}
                  className="w-full px-3 py-2 border-2 border-slate-200 rounded-xl text-sm focus:border-pharmacy-500 transition-colors bg-white"
                  required
                >
                  <option value="">-- Select Section --</option>
                  {sections.filter(s => !userSections.some(us => us.section_name === s.name)).map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
                
                <select
                  value={assignData.permission_level} onChange={e => setAssignData({ ...assignData, permission_level: e.target.value })}
                  className="w-full px-3 py-2 border-2 border-slate-200 rounded-xl text-sm focus:border-pharmacy-500 transition-colors bg-white"
                >
                  <option value="READ">Read Only</option>
                  <option value="WRITE">Read & Write</option>
                  <option value="ADMIN">Section Admin</option>
                </select>
              </div>

              {assignError && (
                <div className="mb-4 text-red-600 text-sm bg-red-50 border border-red-100 px-3 py-2 rounded-lg flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" /> {assignError}
                </div>
              )}

              <button type="submit" disabled={assigning || !assignData.section_id} className="w-full py-2.5 rounded-xl bg-pharmacy-600 hover:bg-pharmacy-700 text-white font-medium flex justify-center items-center gap-2 disabled:opacity-60 transition-colors">
                {assigning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                Grant Access
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Users List Grid */}
      {loading ? (
        <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-pharmacy-500" /></div>
      ) : users.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-16 flex flex-col items-center gap-4 text-slate-400">
          <Users className="w-12 h-12 opacity-30" />
          <p className="font-medium">No users found.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {users.map(user => (
            <div key={user.id} className="bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow p-5 flex flex-col h-full">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-100 to-indigo-50 text-blue-600 flex items-center justify-center font-bold text-xl uppercase shadow-inner">
                    {user.username.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800 text-lg leading-tight">{user.username}</h3>
                    <p className="text-sm text-slate-500">{user.full_name || 'No full name'}</p>
                  </div>
                </div>
                <div className={`text-[10px] px-2.5 py-1 rounded-md font-bold uppercase tracking-wider ${user.role.name === 'ADMIN' ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-600'}`}>
                  {user.role.name}
                </div>
              </div>
              
              <div className="space-y-2.5 mb-6 flex-1">
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Mail className="w-4 h-4 text-slate-400" />
                  <span className="truncate">{user.email}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <ShieldAlert className="w-4 h-4 text-slate-400" />
                  Status: {user.is_active ? <span className="text-green-600 font-medium">Active</span> : <span className="text-red-500 font-medium">Blocked</span>}
                </div>
              </div>

              <button
                onClick={() => openAssignModal(user)}
                className="w-full py-2.5 rounded-xl border-2 border-slate-100 text-slate-700 font-medium hover:border-pharmacy-500 hover:text-pharmacy-600 hover:bg-pharmacy-50 transition-all flex items-center justify-center gap-2"
              >
                <Building className="w-4 h-4" /> Manage Access
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
