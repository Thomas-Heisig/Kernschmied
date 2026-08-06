import React, { useEffect, useState } from 'react';
import { useAuth } from './AuthProvider';
import { updateOwnProfile } from './auth-api';
import { useUserPanels } from './UserAccountPanels';

export default function UserProfilePanel() {
  const { user, refreshCurrentUser } = useAuth() as any;
  const panels = (() => {
    try {
      return useUserPanels();
    } catch {
      return null as any;
    }
  })();

  if (!user) return <div>Nicht angemeldet</div>;

  const [editing, setEditing] = useState(false);
  const [displayName, setDisplayName] = useState(user.displayName ?? '');
  const [email, setEmail] = useState(user.email ?? '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await updateOwnProfile(undefined, { displayName, email: email || null });
      await refreshCurrentUser();
      setEditing(false);
      setSuccess('Profil erfolgreich gespeichert.');
      window.setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err?.message ?? String(err));
    } finally {
      setSaving(false);
    }
  }

  // reset local edits when user changes or panel reopened
  useEffect(() => {
    setDisplayName(user.displayName ?? '');
    setEmail(user.email ?? '');
  }, [user]);

  const isDirty = displayName !== (user.displayName ?? '') || (email || '') !== (user.email ?? '');

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">Profil</h2>
      {error ? <div className="text-red-600">{error}</div> : null}
      {!editing ? (
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
      ) : (
        <div className="mt-4 space-y-3">
          <div>
            <label className="block text-sm">Anzeigename</label>
            <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} className="w-full rounded border px-2 py-1" />
          </div>
          <div>
            <label className="block text-sm">E-Mail</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded border px-2 py-1" />
          </div>
        </div>
      )}

      <div className="mt-6 space-x-2">
        {!editing ? (
          <>
            <button type="button" onClick={() => setEditing(true)} className="px-3 py-1 bg-sky-600 text-white rounded">Profil bearbeiten</button>
            <button type="button" onClick={() => panels?.openPanel('settings')} className="px-3 py-1 bg-slate-200 dark:bg-slate-700 rounded">Persönliche Einstellungen</button>
          </>
        ) : (
          <>
            <button type="button" disabled={saving || !isDirty} onClick={handleSave} className="px-3 py-1 bg-sky-600 text-white rounded">Speichern</button>
            <button type="button" disabled={saving} onClick={() => { setEditing(false); setDisplayName(user.displayName ?? ''); setEmail(user.email ?? ''); }} className="px-3 py-1 bg-slate-200 dark:bg-slate-700 rounded">Abbrechen</button>
          </>
        )}
      </div>

      <div aria-live="polite" className="sr-only">
        {success ?? error}
      </div>
    </div>
  );
}
