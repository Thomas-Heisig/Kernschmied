import React, { useCallback, useRef, useState } from 'react';
import { useAuth } from './AuthProvider';
import { useUserPanels } from './UserAccountPanels';

function initialsFrom(name: string | undefined) {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export default function UserMenu() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);
  const toggleRef = useRef<HTMLButtonElement | null>(null);
  const itemsRef = useRef<Array<HTMLButtonElement | null>>([]);

  const onToggle = useCallback(() => setOpen((s) => !s), []);
  const panels = (() => {
    try {
      return useUserPanels();
    } catch {
      return null as any;
    }
  })();

  // outside click and keyboard handling
  React.useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (!ref.current) return;
      if (!ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
      if (!open) return;
      const items = itemsRef.current;
      const idx = items.findIndex((el) => el === document.activeElement);
      if (e.key === 'ArrowDown') {
        const next = (idx + 1) % items.length;
        items[next]?.focus();
        e.preventDefault();
      } else if (e.key === 'ArrowUp') {
        const prev = (idx - 1 + items.length) % items.length;
        items[prev]?.focus();
        e.preventDefault();
      }
    }

    document.addEventListener('mousedown', onDoc);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDoc);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const handleLogout = useCallback(async () => {
    try {
      await logout();
    } catch {
      // ignore
    }
  }, [logout]);

  const displayName = user?.displayName ?? user?.username ?? 'Gast';

  function onToggleKey(e: React.KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onToggle();
    }
  }

  return (
    <div className="relative" ref={ref}>
      <button
        ref={toggleRef}
        type="button"
        onClick={onToggle}
        onKeyDown={onToggleKey}
        aria-haspopup="menu"
        aria-expanded={open}
        className="inline-flex items-center gap-2 rounded-lg px-2 py-1 hover:bg-surface-hover"
      >
        <div className="h-8 w-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-sm font-semibold text-slate-800 dark:text-white">
          {initialsFrom(displayName)}
        </div>
        <div className="hidden sm:flex flex-col items-start text-left">
          <div className="text-sm font-medium text-gray-900 dark:text-white">{displayName}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400">{user?.username ?? ''}</div>
        </div>
        {user?.developmentSession ? (
          <div className="ml-2 text-xs text-amber-600 font-semibold">DEV</div>
        ) : null}
      </button>

      {open ? (
        <div role="menu" className="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-800 border border-border shadow-lg rounded-md py-1 z-50">
          <button ref={(el) => (itemsRef.current[0] = el)} role="menuitem" onClick={() => { panels?.openPanel('profile'); setOpen(false); toggleRef.current?.focus(); }} className="w-full text-left px-3 py-2 text-sm hover:bg-surface-hover">Profil</button>
          <button ref={(el) => (itemsRef.current[1] = el)} role="menuitem" onClick={() => { panels?.openPanel('settings'); setOpen(false); toggleRef.current?.focus(); }} className="w-full text-left px-3 py-2 text-sm hover:bg-surface-hover">Persönliche Einstellungen</button>
          <button ref={(el) => (itemsRef.current[2] = el)} role="menuitem" onClick={() => { panels?.openPanel('sessions'); setOpen(false); toggleRef.current?.focus(); }} className="w-full text-left px-3 py-2 text-sm hover:bg-surface-hover">Sessions</button>
          {user?.passwordLoginAvailable ? (
            <button ref={(el) => (itemsRef.current[3] = el)} role="menuitem" onClick={() => { panels?.openPanel('change-password'); setOpen(false); toggleRef.current?.focus(); }} className="w-full text-left px-3 py-2 text-sm hover:bg-surface-hover">Passwort ändern</button>
          ) : null}
          <div className="border-t my-1" />
          {user?.developmentSession ? (
            <div className="px-3 py-2 text-sm text-amber-700">Development-Modus (aktiv)</div>
          ) : null}
          <div className="border-t my-1" />
          <button ref={(el) => (itemsRef.current[4] = el)} role="menuitem" onClick={handleLogout} className="w-full text-left px-3 py-2 text-sm hover:bg-surface-hover">
            Abmelden
          </button>
        </div>
      ) : null}
    </div>
  );
}
