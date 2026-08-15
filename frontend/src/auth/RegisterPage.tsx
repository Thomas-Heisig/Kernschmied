import React, { useCallback, useState } from 'react';
import { useAuth } from './AuthProvider';

export default function RegisterPage({ onSuccess, onBack }: { onSuccess?: () => void; onBack?: () => void }) {
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
    if (password.length < 12) {
      setError('Das Passwort muss mindestens 12 Zeichen lang sein.');
      return;
    }
    if (password.trim().toLowerCase() === username.trim().toLowerCase()) {
      setError('Das Passwort darf nicht mit dem Benutzernamen übereinstimmen.');
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
    <div className="flex min-h-screen items-center justify-center bg-surface px-4 py-8 dark:bg-slate-950">
    <form onSubmit={handleSubmit} className="w-full max-w-md space-y-4 rounded-lg border border-border bg-white p-6 shadow-xl dark:border-white/10 dark:bg-slate-900">
      <div>
        <h1 className="text-xl font-semibold">Benutzerkonto erstellen</h1>
        <p className="mt-1 text-sm text-text-muted">Registriere dich für deinen persönlichen Kernschmied-Zugang.</p>
        <p className="mt-2 rounded-md border border-border bg-surface-hover px-3 py-2 text-sm text-text-muted dark:border-white/10 dark:bg-slate-800">
          Neue Konten starten als Gast mit Zugriff auf den eigenen Bereich und öffentliche Inhalte. Ein Administrator kann den Zugang später auf Intern erhöhen.
        </p>
      </div>
      {error && <div role="alert" className="rounded-md bg-danger-soft px-3 py-2 text-sm text-danger">{error}</div>}
      <div>
        <label htmlFor="register-username" className="block text-sm font-medium">Benutzername</label>
        <input id="register-username" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} className="mt-1 block w-full rounded-md border border-border px-3 py-2 dark:border-white/10 dark:bg-slate-800" />
      </div>
      <div>
        <label htmlFor="register-display-name" className="block text-sm font-medium">Anzeigename</label>
        <input id="register-display-name" value={displayName} onChange={(e) => setDisplayName(e.target.value)} className="mt-1 block w-full rounded-md border border-border px-3 py-2 dark:border-white/10 dark:bg-slate-800" />
      </div>
      <div>
        <label htmlFor="register-email" className="block text-sm font-medium">E-Mail (optional)</label>
        <input id="register-email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1 block w-full rounded-md border border-border px-3 py-2 dark:border-white/10 dark:bg-slate-800" />
      </div>
      <div>
        <label htmlFor="register-password" className="block text-sm font-medium">Passwort</label>
        <input id="register-password" autoComplete="new-password" type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1 block w-full rounded-md border border-border px-3 py-2 dark:border-white/10 dark:bg-slate-800" />
      </div>
      <div>
        <label htmlFor="register-password-confirmation" className="block text-sm font-medium">Passwort bestätigen</label>
        <input id="register-password-confirmation" autoComplete="new-password" type={showPassword ? 'text' : 'password'} value={passwordConfirm} onChange={(e) => setPasswordConfirm(e.target.value)} className="mt-1 block w-full rounded-md border border-border px-3 py-2 dark:border-white/10 dark:bg-slate-800" />
      </div>
      {registrationRequiresInvitation && (
        <div>
          <label className="block text-sm font-medium">Einladungscode</label>
          <input value={invite} onChange={(e) => setInvite(e.target.value)} className="mt-1 block w-full rounded-md border border-border px-3 py-2 dark:border-white/10 dark:bg-slate-800" />
        </div>
      )}
      <div className="flex items-center">
        <label className="inline-flex items-center">
          <input type="checkbox" checked={showPassword} onChange={() => setShowPassword((s) => !s)} />
          <span className="ml-2 text-sm">Passwort anzeigen</span>
        </label>
      </div>
      <div className="flex items-center justify-between gap-3">
        <button type="button" onClick={onBack} className="rounded-md px-4 py-2 text-sm hover:bg-surface-hover">Zur Anmeldung</button>
        <button disabled={isSubmitting} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
          {isSubmitting ? 'Sende...' : 'Registrieren'}
        </button>
      </div>
    </form>
    </div>
  );
}
