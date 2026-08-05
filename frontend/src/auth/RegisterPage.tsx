import React, { useCallback, useState } from 'react';
import { useAuth } from './AuthProvider';

export default function RegisterPage({ onSuccess }: { onSuccess?: () => void }) {
  const { register, registrationAvailable, registrationRequiresInvitation } = useAuth();
  const [username, setUsername] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [invite, setInvite] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!registrationAvailable) return;
    setError(null);
    if (!username.trim() || !displayName.trim() || !password) {
      setError('Bitte alle Pflichtfelder ausfüllen.');
      return;
    }
    if (password !== passwordConfirm) {
      setError('Passwörter stimmen nicht überein.');
      return;
    }
    setIsSubmitting(true);
    try {
      await register({
        username: username.trim(),
        displayName: displayName.trim(),
        email: email ? email.trim() : null,
        password,
        passwordConfirmation: passwordConfirm,
        invitationToken: invite || null,
      } as any);

      onSuccess?.();
    } catch (err: any) {
      setError(err?.message ?? String(err));
    } finally {
      setIsSubmitting(false);
    }
  }, [username, displayName, email, password, passwordConfirm, invite, register, registrationAvailable, onSuccess]);

  if (!registrationAvailable) {
    return <div>Registrierung ist nicht verfügbar.</div>;
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-md mx-auto space-y-4">
      {error && <div className="text-red-600">{error}</div>}
      <div>
        <label className="block text-sm font-medium">Benutzername</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} className="mt-1 block w-full" />
      </div>
      <div>
        <label className="block text-sm font-medium">Anzeigename</label>
        <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} className="mt-1 block w-full" />
      </div>
      <div>
        <label className="block text-sm font-medium">E-Mail (optional)</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1 block w-full" />
      </div>
      <div>
        <label className="block text-sm font-medium">Passwort</label>
        <input type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1 block w-full" />
      </div>
      <div>
        <label className="block text-sm font-medium">Passwort bestätigen</label>
        <input type={showPassword ? 'text' : 'password'} value={passwordConfirm} onChange={(e) => setPasswordConfirm(e.target.value)} className="mt-1 block w-full" />
      </div>
      {registrationRequiresInvitation && (
        <div>
          <label className="block text-sm font-medium">Einladungscode</label>
          <input value={invite} onChange={(e) => setInvite(e.target.value)} className="mt-1 block w-full" />
        </div>
      )}
      <div className="flex items-center">
        <label className="inline-flex items-center">
          <input type="checkbox" checked={showPassword} onChange={() => setShowPassword((s) => !s)} />
          <span className="ml-2 text-sm">Passwort anzeigen</span>
        </label>
      </div>
      <div>
        <button disabled={isSubmitting} className="px-4 py-2 bg-blue-600 text-white rounded">
          {isSubmitting ? 'Sende...' : 'Registrieren'}
        </button>
      </div>
    </form>
  );
}
