import React, { useState } from 'react';
import { useAuth } from './AuthProvider';

export default function UserSettingsPanel() {
  const { user } = useAuth();
  const [theme, setTheme] = useState('system');

  if (!user) return <div>Nicht angemeldet</div>;

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">Persönliche Einstellungen</h2>
      <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">Die serverseitige Speicherung persönlicher Einstellungen wird noch vorbereitet.</p>

      <div className="mt-4 space-y-4">
        <div>
          <label className="block text-sm mb-1">Theme</label>
          <select value={theme} onChange={(e) => setTheme(e.target.value)} className="rounded border px-2 py-1">
            <option value="system">System</option>
            <option value="light">Hell</option>
            <option value="dark">Dunkel</option>
          </select>
        </div>

        <div>
          <label className="block text-sm mb-1">Sprache</label>
          <select className="rounded border px-2 py-1">
            <option>Deutsch</option>
          </select>
        </div>
      </div>

      <div className="mt-6">
        <button disabled className="px-3 py-1 bg-slate-400 text-white rounded">Speichern (nicht verfügbar)</button>
        <button className="ml-2 px-3 py-1 bg-slate-200 dark:bg-slate-700 rounded">Zurücksetzen</button>
      </div>
    </div>
  );
}
