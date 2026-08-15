import { useEffect, useState } from 'react';
import { KeyRound, LoaderCircle, Plus, RefreshCw, Save, Trash2, UserRoundCog } from 'lucide-react';

import {
  createManagedUser,
  deleteManagedUser,
  listManagedUsers,
  resetManagedUserPassword,
  updateManagedUser,
  type AccessLevel,
  type ManagedUser,
} from './auth-api';

export default function UserAdministrationPanel() {
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [selectedId, setSelectedId] = useState<string | 'new'>('new');
  const [username, setUsername] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [accessLevel, setAccessLevel] = useState<AccessLevel>('guest');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedUser = users.find((user) => user.id === selectedId) ?? null;

  async function loadUsers() {
    setLoading(true);
    setError(null);
    try {
      setUsers(await listManagedUsers());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Benutzer konnten nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadUsers();
  }, []);

  useEffect(() => {
    if (!selectedUser) {
      setUsername('');
      setDisplayName('');
      setEmail('');
      setPassword('');
      setIsActive(true);
      setAccessLevel('guest');
      return;
    }
    setUsername(selectedUser.username);
    setDisplayName(selectedUser.displayName);
    setEmail(selectedUser.email ?? '');
    setPassword('');
    setIsActive(selectedUser.isActive);
    setAccessLevel(selectedUser.accessLevel);
  }, [selectedUser]);

  async function handleSave() {
    if (!displayName.trim() || (selectedId === 'new' && !username.trim())) {
      setError('Benutzername und Anzeigename sind erforderlich.');
      return;
    }
    if (selectedId === 'new' && password && password.length < 12) {
      setError('Das Startpasswort muss mindestens 12 Zeichen lang sein.');
      return;
    }
    if (
      selectedId === 'new'
      && password
      && password.trim().toLowerCase() === username.trim().toLowerCase()
    ) {
      setError('Das Startpasswort darf nicht mit dem Benutzernamen übereinstimmen.');
      return;
    }
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      if (selectedId === 'new') {
        const result = await createManagedUser({
          username: username.trim(),
          displayName: displayName.trim(),
          email: email.trim() || null,
          password: password || null,
          generatePassword: !password,
          requirePasswordChange: true,
          accessLevel,
        });
        setMessage(
          result.temporaryPassword
            ? `Benutzer erstellt. Temporäres Passwort: ${result.temporaryPassword}`
            : 'Benutzer wurde erstellt.',
        );
        setSelectedId(result.user.id);
      } else {
        await updateManagedUser(selectedId, {
          displayName: displayName.trim(),
          email: email.trim() || null,
          isActive,
          accessLevel,
        });
        setMessage('Benutzerdaten wurden gespeichert.');
      }
      await loadUsers();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Benutzer konnte nicht gespeichert werden.');
    } finally {
      setSaving(false);
    }
  }

  async function handlePasswordReset() {
    if (selectedId === 'new') return;
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const generatedPassword = await resetManagedUserPassword(selectedId, password || null);
      setPassword('');
      setMessage(
        generatedPassword
          ? `Temporäres Passwort: ${generatedPassword}`
          : 'Passwort wurde gesetzt; bestehende Sitzungen wurden beendet.',
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Passwort konnte nicht zurückgesetzt werden.');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (selectedId === 'new' || selectedUser?.isSystem) return;
    if (!globalThis.confirm(`Benutzer „${selectedUser?.displayName}“ dauerhaft löschen?`)) {
      return;
    }
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await deleteManagedUser(selectedId);
      setSelectedId('new');
      setMessage('Benutzer wurde dauerhaft gelöscht.');
      await loadUsers();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Benutzer konnte nicht gelöscht werden.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="grid min-h-128 grid-cols-1 overflow-hidden rounded-lg border border-border md:grid-cols-[15rem_minmax(0,1fr)] dark:border-white/10">
      <aside className="border-b border-border bg-surface-hover/60 p-3 md:border-b-0 md:border-r dark:border-white/10 dark:bg-slate-900/40">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-sm font-semibold"><UserRoundCog size={17} /> Benutzer</h2>
          <button type="button" onClick={() => void loadUsers()} className="rounded-md p-1.5 hover:bg-white dark:hover:bg-slate-700" aria-label="Benutzer aktualisieren"><RefreshCw size={15} /></button>
        </div>
        <button type="button" onClick={() => setSelectedId('new')} className="mb-3 flex w-full items-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-white"><Plus size={15} /> Neuer Benutzer</button>
        {loading ? <LoaderCircle className="mx-auto animate-spin text-text-muted" size={18} /> : (
          <div className="space-y-1" role="listbox" aria-label="Benutzerkonten">
            {users.map((user) => (
              <button
                key={user.id}
                type="button"
                role="option"
                aria-selected={selectedId === user.id}
                onClick={() => setSelectedId(user.id)}
                className={`w-full rounded-md px-3 py-2 text-left text-sm ${selectedId === user.id ? 'bg-white shadow-sm dark:bg-slate-700' : 'hover:bg-white/70 dark:hover:bg-slate-800'}`}
              >
                <span className="block truncate font-medium">{user.displayName}</span>
                <span className="block truncate text-xs text-text-muted">@{user.username}{user.isActive ? '' : ' · deaktiviert'}</span>
              </button>
            ))}
          </div>
        )}
      </aside>

      <section className="min-w-0 p-5">
        <h2 className="text-lg font-semibold">{selectedId === 'new' ? 'Benutzer anlegen' : 'Benutzerdaten bearbeiten'}</h2>
        <p className="mt-1 text-sm text-text-muted">Kontodaten und Passwortzugang zentral verwalten.</p>
        {error ? <div role="alert" className="mt-4 rounded-md bg-danger-soft px-3 py-2 text-sm text-danger">{error}</div> : null}
        {message ? <div role="status" className="mt-4 rounded-md bg-success/10 px-3 py-2 text-sm text-success">{message}</div> : null}

        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <label className="text-sm font-medium">Benutzername
            <input value={username} disabled={selectedId !== 'new'} onChange={(event) => setUsername(event.target.value)} className="mt-1 w-full rounded-md border border-border bg-white px-3 py-2 disabled:bg-surface-hover dark:border-white/10 dark:bg-slate-900" />
          </label>
          <label className="text-sm font-medium">Anzeigename
            <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} className="mt-1 w-full rounded-md border border-border bg-white px-3 py-2 dark:border-white/10 dark:bg-slate-900" />
          </label>
          <label className="text-sm font-medium sm:col-span-2">E-Mail
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} className="mt-1 w-full rounded-md border border-border bg-white px-3 py-2 dark:border-white/10 dark:bg-slate-900" />
          </label>
          <label className="text-sm font-medium sm:col-span-2">Zugriffsstufe
            <select
              value={accessLevel}
              disabled={selectedUser?.isSystem}
              onChange={(event) => setAccessLevel(event.target.value as AccessLevel)}
              className="mt-1 w-full rounded-md border border-border bg-white px-3 py-2 disabled:bg-surface-hover dark:border-white/10 dark:bg-slate-900"
            >
              <option value="guest">Gast · eigene und öffentliche Bereiche</option>
              <option value="internal">Intern · zusätzlich interne Bereiche</option>
              <option value="admin">Administrator · vollständiger Zugriff</option>
            </select>
          </label>
          <label className="text-sm font-medium sm:col-span-2">{selectedId === 'new' ? 'Startpasswort (leer = generieren)' : 'Neues Passwort (leer = generieren)'}
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="mt-1 w-full rounded-md border border-border bg-white px-3 py-2 dark:border-white/10 dark:bg-slate-900" />
          </label>
          {selectedId !== 'new' ? (
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={isActive} disabled={selectedUser?.isSystem} onChange={(event) => setIsActive(event.target.checked)} /> Konto aktiv</label>
          ) : null}
        </div>

        <div className="mt-6 flex flex-wrap gap-2">
          <button type="button" disabled={saving} onClick={() => void handleSave()} className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-50"><Save size={15} /> {saving ? 'Speichert…' : 'Speichern'}</button>
          {selectedId !== 'new' ? (
            <button type="button" disabled={saving || selectedUser?.isSystem} onClick={() => void handlePasswordReset()} className="inline-flex items-center gap-2 rounded-md border border-border px-4 py-2 text-sm font-medium hover:bg-surface-hover disabled:opacity-50 dark:border-white/10"><KeyRound size={15} /> Passwort zurücksetzen</button>
          ) : null}
          {selectedId !== 'new' ? (
            <button type="button" disabled={saving || selectedUser?.isSystem} onClick={() => void handleDelete()} className="inline-flex items-center gap-2 rounded-md border border-danger px-4 py-2 text-sm font-medium text-danger hover:bg-danger-soft disabled:opacity-50"><Trash2 size={15} /> Benutzer löschen</button>
          ) : null}
        </div>
      </section>
    </div>
  );
}