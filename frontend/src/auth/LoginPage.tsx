import React, { useState } from 'react';
import { useAuth } from './AuthProvider';
import { toast } from 'sonner';

export default function LoginPage({ onSuccess }: { onSuccess?: () => void }) {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await login(username, password);
      toast.success('Angemeldet');
      onSuccess?.();
    } catch (err: any) {
      toast.error('Anmeldung fehlgeschlagen: ' + String(err?.message ?? err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-md mx-auto p-4 bg-white rounded shadow">
      <h2 className="text-lg font-semibold mb-4">Anmelden</h2>
      <form onSubmit={handleSubmit}>
        <label className="block mb-2">
          <div className="text-sm mb-1">Benutzername / E-Mail</div>
          <input
            className="w-full rounded border px-2 py-1"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoFocus
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
            {loading ? 'Lädt…' : 'Anmelden'}
          </button>
        </div>
      </form>
    </div>
  );
}
