import React, { createContext, useContext, useEffect, useState } from 'react';
import { apiGet, apiPost } from '../api/client';

type User = { id: string; display_name?: string; email?: string } | null;

type AuthContextValue = {
  user: User;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User>(null);
  const [loading, setLoading] = useState(true);

  async function fetchUser() {
    try {
      const me = await apiGet<any>('/me');
      setUser(me ?? null);
    } catch (err) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void fetchUser();
  }, []);

  async function login(username: string, password: string) {
    setLoading(true);
    try {
      await apiPost('/auth/login', { username, password }, { credentials: 'include' });
      await fetchUser();
    } finally {
      setLoading(false);
    }
  }

  async function logout() {
    setLoading(true);
    try {
      await apiPost('/auth/logout', undefined, { credentials: 'include' });
    } catch (err) {
      // ignore
    } finally {
      setUser(null);
      setLoading(false);
    }
  }

  const value: AuthContextValue = {
    user,
    loading,
    login,
    logout,
    refresh: fetchUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export default AuthProvider;
