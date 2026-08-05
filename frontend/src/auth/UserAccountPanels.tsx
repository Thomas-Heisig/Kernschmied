import React, { createContext, useContext, useMemo, useState, useEffect, useRef } from 'react';
import UserProfilePanel from './UserProfilePanel';
import UserSettingsPanel from './UserSettingsPanel';
import UserSessionsPanel from './UserSessionsPanel';
import UserChangePasswordPanel from './UserChangePasswordPanel';

export type UserPanel = 'profile' | 'settings' | 'sessions' | 'change-password' | null;

type PanelsContext = {
  openPanel: (p: UserPanel) => void;
  closePanel: () => void;
  activePanel: UserPanel;
};

const ctx = createContext<PanelsContext | undefined>(undefined);

export function useUserPanels(): PanelsContext {
  const c = useContext(ctx);
  if (!c) throw new Error('useUserPanels must be used within UserAccountPanels');
  return c;
}

export function UserAccountPanelsProvider({ children }: { children: React.ReactNode }) {
  const [active, setActive] = useState<UserPanel>(null);
  const lastFocusedRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape' && active !== null) {
        setActive(null);
      }
    }
    if (active !== null) {
      document.addEventListener('keydown', onKey);
    }
    return () => document.removeEventListener('keydown', onKey);
  }, [active]);

  const value = useMemo(() => ({
    openPanel: (p: UserPanel) => {
      try {
        const el = document.activeElement as HTMLElement | null;
        lastFocusedRef.current = el ?? null;
      } catch {
        lastFocusedRef.current = null;
      }
      setActive(p);
    },
    closePanel: () => {
      setActive(null);
      try {
        if (lastFocusedRef.current && typeof lastFocusedRef.current.focus === 'function') {
          lastFocusedRef.current.focus();
        }
      } catch {
        // ignore
      }
    },
    activePanel: active,
  }), [active]);

  return (
    <ctx.Provider value={value}>
      {children}

      {active === 'profile' && (
        <div className="fixed inset-0 z-1000 flex items-start justify-center p-4">
          <div className="absolute inset-0 bg-black/40" onClick={() => setActive(null)} />
          <div className="relative w-full max-w-md bg-white dark:bg-slate-800 rounded shadow-lg max-h-screen overflow-auto">
            <div className="p-4">
              <button className="float-right" onClick={() => value.closePanel()}>Schließen</button>
              <UserProfilePanel />
            </div>
          </div>
        </div>
      )}

      {active === 'settings' && (
        <div className="fixed inset-0 z-1000 flex items-start justify-center p-4">
          <div className="absolute inset-0 bg-black/40" onClick={() => setActive(null)} />
          <div className="relative w-full max-w-md bg-white dark:bg-slate-800 rounded shadow-lg max-h-screen overflow-auto">
            <div className="p-4">
              <button className="float-right" onClick={() => value.closePanel()}>Schließen</button>
              <UserSettingsPanel />
            </div>
          </div>
        </div>
      )}

      {active === 'sessions' && (
        <div className="fixed inset-0 z-1000 flex items-start justify-center p-4">
          <div className="absolute inset-0 bg-black/40" onClick={() => setActive(null)} />
          <div className="relative w-full max-w-2xl bg-white dark:bg-slate-800 rounded shadow-lg max-h-screen overflow-auto">
            <div className="p-4">
              <button className="float-right" onClick={() => value.closePanel()}>Schließen</button>
              <UserSessionsPanel onClose={() => value.closePanel()} />
            </div>
          </div>
        </div>
      )}

      {active === 'change-password' && (
        <div className="fixed inset-0 z-1000 flex items-start justify-center p-4">
          <div className="absolute inset-0 bg-black/40" onClick={() => setActive(null)} />
          <div className="relative w-full max-w-md bg-white dark:bg-slate-800 rounded shadow-lg max-h-screen overflow-auto">
            <div className="p-4">
              <button className="float-right" onClick={() => value.closePanel()}>Schließen</button>
              <UserChangePasswordPanel onClose={() => value.closePanel()} />
            </div>
          </div>
        </div>
      )}
    </ctx.Provider>
  );
}

export default UserAccountPanelsProvider;
