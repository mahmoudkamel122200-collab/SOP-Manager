import React, { createContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import api from '../services/api';

// ─── Types ────────────────────────────────────────────────────────────────────
export interface User {
  id: string;
  username: string;
  full_name?: string;
  email?: string;
  role: 'ADMIN' | 'EMPLOYEE';
  is_active?: boolean;
}

export interface Section {
  id: string;
  name: string;
}

interface AuthContextType {
  user: User | null;
  section: Section | null;
  loading: boolean;
  login: (token: string, userData: User, sectionData?: Section) => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ─── Provider ─────────────────────────────────────────────────────────────────
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser]       = useState<User | null>(null);
  const [section, setSection] = useState<Section | null>(null);
  const [loading, setLoading] = useState(true);

  // Rehydrate auth from localStorage on first load
  useEffect(() => {
    const rehydrate = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const res  = await api.get('/auth/me');
        const data = res.data?.data ?? res.data;
        setUser({
          id:        data.id,
          username:  data.username,
          full_name: data.full_name,
          email:     data.email,
          role:      data.role,
          is_active: data.is_active,
        });
        const stored = localStorage.getItem('section');
        if (stored) setSection(JSON.parse(stored));
      } catch {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('section');
      } finally {
        setLoading(false);
      }
    };
    rehydrate();
  }, []);

  const login = useCallback(
    (token: string, userData: User, sectionData?: Section) => {
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
      if (sectionData) {
        localStorage.setItem('section', JSON.stringify(sectionData));
        setSection(sectionData);
      }
    },
    []
  );

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // ignore — clear locally regardless
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('section');
      setUser(null);
      setSection(null);
      window.location.href = '/login';
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, section, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
