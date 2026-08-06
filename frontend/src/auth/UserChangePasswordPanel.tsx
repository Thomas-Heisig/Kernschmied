import React, { useState } from 'react';
import { changePassword } from './auth-api';
import { useAuth } from './AuthProvider';

function passwordStrength(pw: string) {
  let score = 0;
  if (pw.length >= 12) score += 1;
  if (/[A-Z]/.test(pw)) score += 1;
  if (/[0-9]/.test(pw)) score += 1;
  if (/[^A-Za-z0-9]/.test(pw)) score += 1;
  return score;
}

export default function UserChangePasswordPanel({ onClose }: { onClose?: () => void }) {
  const { refreshCurrentUser, markUnauthenticated } = useAuth() as any;
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [repeatPassword, setRepeatPassword] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      if (newPassword !== repeatPassword) throw new Error('Die Passwörter stimmen nicht überein.');
      await changePassword(undefined, { currentPassword, newPassword, revokeOtherSessions: false });
      setSuccess('Passwort geändert');
      // Optionally refresh user context
      await refreshCurrentUser();
      setTimeout(() => {
        setSuccess(null);
        onClose && onClose();
      }, 1200);
    } catch (err: any) {
      setError(err?.message ?? String(err));
    } finally {
      setSaving(false);
    }
  }

  const strength = passwordStrength(newPassword);

  return (
    <div className="p-4 max-h-[80vh] overflow-auto">
      <h2 className="text-lg font-semibold">Passwort ändern</h2>
      {error && <div className="text-red-600 mt-2">{error}</div>}
      {success && <div className="text-green-600 mt-2">{success}</div>}

      <div className="mt-4 space-y-3">
        <div>
          <label className="block text-sm">Aktuelles Passwort</label>
          <input aria-label="aktuelles Passwort" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} className="w-full rounded border px-2 py-1" />
        </div>
        <div>
          <label className="block text-sm">Neues Passwort</label>
          <input aria-label="neues Passwort" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="w-full rounded border px-2 py-1" />
          <div className="text-xs text-gray-600 mt-1">Stärke: {['sehr schwach', 'schwach', 'mittel', 'stark', 'sehr stark'][strength]}</div>
        </div>
        <div>
          <label className="block text-sm">Neues Passwort wiederholen</label>
          <input aria-label="neues Passwort wiederholen" type="password" value={repeatPassword} onChange={(e) => setRepeatPassword(e.target.value)} className="w-full rounded border px-2 py-1" />
        </div>
      </div>

      <div className="mt-6">
        <button type="button" disabled={saving} onClick={() => void handleSave()} className="px-3 py-1 bg-sky-600 text-white rounded">{saving ? 'Speichert…' : 'Passwort ändern'}</button>
        <button type="button" disabled={saving} onClick={() => onClose && onClose()} className="ml-2 px-3 py-1 bg-slate-200 dark:bg-slate-700 rounded">Abbrechen</button>
      </div>
    </div>
  );
}
