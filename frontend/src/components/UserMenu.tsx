import React, { useState } from 'react';
import { useAuth } from '../auth/AuthProvider';

export default function UserMenu() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  if (!user) {
    return (
      <div>
        <a href="/login" className="px-3 py-1 rounded bg-sky-600 text-white">
          Anmelden
        </a>
      </div>
    );
  }

  const display = user.display_name ?? user.email ?? 'Benutzer';

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((s) => !s)}
        className="flex items-center gap-2 px-3 py-1 rounded hover:bg-slate-100"
        aria-haspopup
        aria-expanded={open}
      >
        <div className="w-8 h-8 rounded-full bg-sky-600 text-white flex items-center justify-center">{display.charAt(0).toUpperCase()}</div>
        <div className="hidden sm:block">{display}</div>
      </button>

      {open ? (
        <div className="absolute right-0 mt-2 w-48 bg-white border rounded shadow z-20">
          <ul className="p-2">
            <li>
              <a href="/profile" className="block px-2 py-1 hover:bg-slate-50">
                Profil
              </a>
            </li>
            <li>
              <a href="/preferences" className="block px-2 py-1 hover:bg-slate-50">
                Einstellungen
              </a>
            </li>
            <li>
              <button
                className="w-full text-left px-2 py-1 hover:bg-slate-50"
                onClick={async () => {
                  setOpen(false);
                  await logout();
                }}
              >
                Abmelden
              </button>
            </li>
          </ul>
        </div>
      ) : null}
    </div>
  );
}
