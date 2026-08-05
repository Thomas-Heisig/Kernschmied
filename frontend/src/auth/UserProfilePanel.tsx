import React from 'react';
import { useAuth } from './AuthProvider';

export default function UserProfilePanel() {
  const { user } = useAuth();

  if (!user) return <div>Nicht angemeldet</div>;

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">Profil</h2>
      <div className="mt-4 space-y-2 text-sm text-gray-700 dark:text-gray-300">
        <div>
          <strong>Anzeigename:</strong> {user.displayName ?? 'Nicht angegeben'}
        </div>
        <div>
          <strong>Benutzername:</strong> {user.username ?? 'Nicht angegeben'}
        </div>
        <div>
          <strong>E-Mail:</strong> {user.email ?? 'Nicht angegeben'}
        </div>
        <div>
          <strong>Tenant:</strong> {user.tenant?.displayName ?? 'Nicht angegeben'}
        </div>
        <div>
          <strong>Benutzer-ID:</strong> {user.id}
        </div>
        <div>
          <strong>Sitzungstyp:</strong> {user.authenticated ? 'Authentifiziert' : 'Gast'}
        </div>
        <div>
          <strong>Development-Status:</strong> {user.developmentSession ? 'Ja' : 'Nein'}
        </div>
      </div>
      <div className="mt-6 space-x-2">
        <button className="px-3 py-1 bg-sky-600 text-white rounded">Profil bearbeiten</button>
        <button className="px-3 py-1 bg-slate-200 dark:bg-slate-700 rounded">Persönliche Einstellungen</button>
      </div>
    </div>
  );
}
