import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FlaskConical,
  ShieldCheck,
  User,
  ChevronLeft,
  Loader2,
  AlertTriangle,
} from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

// ─── Types ────────────────────────────────────────────────────────────────────
type FlowStep = 'ROLE_SELECT' | 'SECTION_SELECT' | 'LOGIN_FORM';

interface SectionItem {
  id: string;
  name: string;
  permission_level?: string;
}

const FALLBACK_SECTIONS: SectionItem[] = [
  { id: '00000000-0000-0000-0002-000000000001', name: 'Production' },
  { id: '00000000-0000-0000-0002-000000000002', name: 'Labs' },
  { id: '00000000-0000-0000-0002-000000000003', name: 'Warehouse' },
  { id: '00000000-0000-0000-0002-000000000004', name: 'Quality' },
];

// ─── Animation variants ───────────────────────────────────────────────────────
const slide = {
  initial: { opacity: 0, x: 24 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.22 } },
  exit:    { opacity: 0, x: -24, transition: { duration: 0.18 } },
};

// ─── Section icon helpers ─────────────────────────────────────────────────────
const SECTION_COLORS: Record<string, string> = {
  production: 'bg-blue-50 text-blue-600 border-blue-100 hover:border-blue-400 hover:bg-blue-50',
  labs:       'bg-purple-50 text-purple-600 border-purple-100 hover:border-purple-400 hover:bg-purple-50',
  warehouse:  'bg-amber-50 text-amber-600 border-amber-100 hover:border-amber-400 hover:bg-amber-50',
  quality:    'bg-green-50 text-green-600 border-green-100 hover:border-green-400 hover:bg-green-50',
};
const sectionColor = (name: string) =>
  SECTION_COLORS[name.toLowerCase()] ??
  'bg-pharmacy-50 text-pharmacy-600 border-pharmacy-100 hover:border-pharmacy-400 hover:bg-pharmacy-50';

// ─── Component ────────────────────────────────────────────────────────────────
export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [step, setStep]       = useState<FlowStep>('ROLE_SELECT');
  const [role, setRole]       = useState<'ADMIN' | 'EMPLOYEE' | null>(null);
  const [selectedSection, setSelectedSection] = useState<SectionItem | null>(null);

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);

  // ── Step 1: Role click ─────────────────────────────────────────────────────
  const handleRoleClick = (r: 'ADMIN' | 'EMPLOYEE') => {
    setRole(r);
    setError('');
    if (r === 'ADMIN') {
      setStep('LOGIN_FORM');
    } else {
      setStep('SECTION_SELECT');
    }
  };

  // ── Step 2: Section select (Employee only) ──────────────────────────────────
  const handleSectionSelect = (sec: SectionItem) => {
    setSelectedSection(sec);
    setError('');
    setStep('LOGIN_FORM');
  };

  // ── Step 3: Login submit ───────────────────────────────────────────────────
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // POST /auth/login
      const loginRes  = await api.post('/auth/login', { username, password });
      const loginData = loginRes.data?.data ?? loginRes.data;
      const token: string = loginData.access_token;

      // Store token so requests work
      localStorage.setItem('token', token);

      // GET /auth/me
      const meRes  = await api.get('/auth/me');
      const userData = meRes.data?.data ?? meRes.data;

      // ── Admin path ────────────────────────────────────────────────────────
      if (role === 'ADMIN') {
        if (userData.role !== 'ADMIN') {
          setError('Access denied. This account is not an admin.');
          localStorage.removeItem('token');
          return;
        }
        login(token, { id: userData.id, username: userData.username, role: userData.role });
        navigate('/admin/dashboard', { replace: true });
        return;
      }

      // ── Employee path — Verify Section Access ───────────────────────────────

      if (!selectedSection) {
        setError('No section selected. Please go back and select a section.');
        localStorage.removeItem('token');
        return;
      }

      try {
        // Check if the user can access the section they selected before login
        const selectRes = await api.post('/auth/select-section', { section_id: selectedSection.id });
        const selectData = selectRes.data?.data ?? selectRes.data;
        const sectionToken: string = selectData.access_token ?? token;

        // Fetch updated user info with the section-scoped token
        localStorage.setItem('token', sectionToken);
        const newMeRes = await api.get('/auth/me');
        const newUserData = newMeRes.data?.data ?? newMeRes.data;

        login(
          sectionToken,
          { id: newUserData.id, username: newUserData.username, role: newUserData.role },
          { id: selectedSection.id, name: selectedSection.name }
        );
        navigate('/employee/dashboard', { replace: true });
      } catch (secErr: any) {
        localStorage.removeItem('token');
        setError(`Access denied. You do not have permission to access the ${selectedSection.name} section.`);
      }

    } catch (err: any) {
      localStorage.removeItem('token');
      setError(
        err.response?.data?.detail ??
        err.response?.data?.message ??
        'Invalid username or password.'
      );
    } finally {
      setLoading(false);
    }
  };

  const goBack = () => {
    setError('');
    if (step === 'LOGIN_FORM' && role === 'EMPLOYEE') {
      setStep('SECTION_SELECT');
    } else {
      setStep('ROLE_SELECT');
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-gradient-to-br from-slate-50 via-teal-50/20 to-blue-50/30 relative overflow-hidden">
      {/* Ambient blobs */}
      <div className="bg-blob bg-blob-1" />
      <div className="bg-blob bg-blob-2" />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="relative z-10 w-full max-w-md"
      >
        {/* ── Logo ─────────────────────────────────────────────────────────── */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-pharmacy-500 to-cyan-500 shadow-xl shadow-pharmacy-500/30 mb-4">
            <FlaskConical className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-extrabold text-slate-800 tracking-tight">PharmaSys</h1>
          <p className="text-slate-400 mt-1 text-sm font-medium">Factory Management System</p>
        </div>

        {/* ── Card ─────────────────────────────────────────────────────────── */}
        <div className="glass-panel rounded-2xl p-8">
          {/* Error banner */}
          <AnimatePresence>
            {error && (
              <motion.div
                key="err"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-5 p-3 bg-red-50 border border-red-100 text-red-600 rounded-xl text-sm flex items-start gap-2"
              >
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence mode="wait">
            {/* ── STEP 1: Role Selection ─────────────────────────────────── */}
            {step === 'ROLE_SELECT' && (
              <motion.div key="role" {...slide} className="space-y-4">
                <h2 className="text-xl font-bold text-slate-700 text-center mb-6">
                  Select Access Level
                </h2>

                <button
                  id="role-admin-btn"
                  onClick={() => handleRoleClick('ADMIN')}
                  className="w-full group flex items-center gap-4 p-5 border-2 border-blue-100 rounded-2xl text-left hover:border-blue-400 hover:bg-blue-50/60 transition-all duration-200"
                >
                  <div className="w-12 h-12 rounded-xl bg-blue-100 group-hover:bg-blue-200 flex items-center justify-center transition-colors shrink-0">
                    <ShieldCheck className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-slate-800">Admin</p>
                    <p className="text-sm text-slate-500">Full system access &amp; management</p>
                  </div>
                </button>

                <button
                  id="role-employee-btn"
                  onClick={() => handleRoleClick('EMPLOYEE')}
                  className="w-full group flex items-center gap-4 p-5 border-2 border-pharmacy-100 rounded-2xl text-left hover:border-pharmacy-400 hover:bg-pharmacy-50/60 transition-all duration-200"
                >
                  <div className="w-12 h-12 rounded-xl bg-pharmacy-100 group-hover:bg-pharmacy-200 flex items-center justify-center transition-colors shrink-0">
                    <User className="w-6 h-6 text-pharmacy-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-slate-800">Employee</p>
                    <p className="text-sm text-slate-500">Section-based access to documents &amp; warehouse</p>
                  </div>
                </button>
              </motion.div>
            )}

            {/* ── STEP 2: Section Selection (Employee) ───────────────────────────── */}
            {step === 'SECTION_SELECT' && (
              <motion.div key="section" {...slide}>
                <button
                  type="button"
                  onClick={goBack}
                  className="flex items-center gap-1 text-sm text-slate-400 hover:text-slate-700 transition-colors mb-4"
                >
                  <ChevronLeft className="w-4 h-4" />
                  Back
                </button>

                <h2 className="text-xl font-bold text-slate-700 text-center mb-1">
                  Select Your Section
                </h2>
                <p className="text-slate-400 text-sm text-center mb-6">
                  Choose the section you are working in today
                </p>

                <div className="grid grid-cols-2 gap-3">
                  {FALLBACK_SECTIONS.map((sec) => (
                    <button
                      key={sec.id}
                      id={`section-${sec.name.toLowerCase()}-btn`}
                      onClick={() => handleSectionSelect(sec)}
                      className={`p-4 border-2 rounded-xl font-semibold text-sm transition-all duration-200 text-center ${sectionColor(sec.name)}`}
                    >
                      {sec.name}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {/* ── STEP 3: Login Form ─────────────────────────────────────── */}
            {step === 'LOGIN_FORM' && (
              <motion.form
                key="login"
                {...slide}
                onSubmit={handleLogin}
                className="space-y-5"
              >
                <button
                  type="button"
                  onClick={goBack}
                  className="flex items-center gap-1 text-sm text-slate-400 hover:text-slate-700 transition-colors mb-1"
                >
                  <ChevronLeft className="w-4 h-4" />
                  Back
                </button>

                <div className="text-center">
                  <h2 className="text-xl font-bold text-slate-700">
                    {role === 'ADMIN' ? 'Admin Login' : `${selectedSection?.name} Login`}
                  </h2>
                  <p className="text-slate-400 text-sm mt-1">
                    {role === 'EMPLOYEE' ? `Enter your credentials to access ${selectedSection?.name}` : 'Enter your admin credentials'}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-600 mb-1.5">
                    Username
                  </label>
                  <input
                    id="login-username"
                    type="text"
                    required
                    autoComplete="username"
                    autoFocus
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Enter your username"
                    className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:border-pharmacy-500 focus:ring-2 focus:ring-pharmacy-500/20 outline-none transition-all text-slate-800"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-600 mb-1.5">
                    Password
                  </label>
                  <input
                    id="login-password"
                    type="password"
                    required
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:border-pharmacy-500 focus:ring-2 focus:ring-pharmacy-500/20 outline-none transition-all text-slate-800"
                  />
                </div>

                <button
                  id="login-submit-btn"
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-pharmacy-600 to-pharmacy-700 hover:from-pharmacy-700 hover:to-pharmacy-800 text-white font-semibold py-3 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-pharmacy-500/25 disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <><Loader2 className="w-5 h-5 animate-spin" /> Verifying…</>
                  ) : (
                    'Continue →'
                  )}
                </button>
              </motion.form>
            )}
          </AnimatePresence>
        </div>

        <p className="text-center text-xs text-slate-400 mt-6">
          PharmaSys &copy; {new Date().getFullYear()} — Secure Factory Management
        </p>
      </motion.div>
    </div>
  );
};
