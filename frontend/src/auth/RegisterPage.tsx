import React, { useState } from 'react';
import { apiPost } from '../api/client';
import { useAuth } from './AuthProvider';
import { toast } from 'sonner';

export default function RegisterPage({ onSuccess }: { onSuccess?: () => void }) {
  const { refresh } = useAuth();
  const [username, setUsername] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await apiPost('/auth/register', { username, password, display_name: displayName || undefined, email: email || undefined }, { credentials: 'include' });
      toast.success('Account erstellt. Bitte anmelden.');
      await refresh();
      onSuccess?.();
    } catch (err: any) {
      toast.error('Registrierung fehlgeschlagen: ' + String(err?.message ?? err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-md mx-auto p-4 bg-white rounded shadow">
      <h2 className="text-lg font-semibold mb-4">Registrieren</h2>
      <form onSubmit={handleSubmit}>
        <label className="block mb-2">
          <div className="text-sm mb-1">Benutzername</div>
          <input
            className="w-full rounded border px-2 py-1"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoFocus
          />
        </label>

        <label className="block mb-2">
          <div className="text-sm mb-1">Anzeigename</div>
          <input
            className="w-full rounded border px-2 py-1"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
        </label>

        <label className="block mb-2">
          <div className="text-sm mb-1">E-Mail</div>
          <input
            type="email"
            className="w-full rounded border px-2 py-1"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>

        <label className="block mb-4">
          <div className="text-sm mb-1">Passwort</div>
          <input
            type="password"
            className="w-full rounded border px-2 py-1"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>

        <div className="flex justify-end gap-2">
          <button type="submit" className="px-4 py-2 bg-sky-600 text-white rounded" disabled={loading}>
            {loading ? 'Lädt…' : 'Registrieren'}
          </button>
        </div>
      </form>
    </div>
  );
}
