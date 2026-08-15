import React, { useEffect, useRef, useState } from 'react';
import { useAuth } from './AuthProvider';
import IconBadge from '../components/common/IconBadge';
import { toast } from 'sonner';

export default function LoginPage({ onSuccess, onRegister }: { onSuccess?: () => void; onRegister?: () => void }) {
  const { login, developmentAdminLogin, developmentLoginAvailable, isSubmitting, error, status, registrationAvailable } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const userRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    userRef.current?.focus();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await login(username.trim(), password);
      toast.success('Angemeldet');
      onSuccess?.();
    } catch (err: any) {
      toast.error('Anmeldung fehlgeschlagen: ' + String(err?.message ?? err));
    }
  }

  async function handleDevLogin() {
    try {
      await developmentAdminLogin();
      toast.success('Development-Administrator angemeldet');
      onSuccess?.();
    } catch (err: any) {
      toast.error('Entwickler-Login fehlgeschlagen: ' + String(err?.message ?? err));
    }
  }

  // Responsive two-column layout on desktop, stacked on mobile
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900 p-6">
      <div className="w-full max-w-6xl bg-white dark:bg-slate-800 rounded-lg shadow-lg overflow-hidden grid grid-cols-1 md:grid-cols-2">
        <div className="p-8 md:p-12 bg-linear-to-b from-white to-slate-50 dark:from-slate-800 dark:to-slate-900">
          <div className="flex items-center gap-4">
            <IconBadge icon={<img src="/favicon.png" alt="Kernschmied" className="h-8 w-8 object-contain" />} size="lg" variant="default" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Kernschmied</h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
                Ihre zentrale Kommunikations- und Assistenzplattform.
              </p>
            </div>
          </div>

          <p className="mt-6 text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
            Chats, Informationen, Projekte und Werkzeuge in einem gemeinsamen,
            sicher kontrollierten Arbeitskontext.
          </p>

          <ul className="mt-6 space-y-3 text-sm text-gray-700 dark:text-gray-300">
            <li>• Schema-gesteuerte Oberfläche</li>
            <li>• Dynamische Hierarchie</li>
            <li>• Lokale und externe KI-Modelle</li>
            <li>• Nachvollziehbare Aktionen</li>
          </ul>

          <div className="mt-8 text-xs text-gray-500 dark:text-gray-400">
            <p>Hinweis: Nur vorhandene Loginmöglichkeiten werden angezeigt.</p>
          </div>
        </div>

        <div className="p-8 md:p-12">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Willkommen zurück</h2>

          <form className="mt-6" onSubmit={handleSubmit}>
            <label className="block">
              <div className="text-sm mb-1 text-gray-700 dark:text-gray-300">Benutzername</div>
              <input
                ref={userRef}
                autoComplete="username"
                className="w-full rounded border px-3 py-2 bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </label>

            <label className="block mt-4">
              <div className="flex items-center justify-between text-sm mb-1 text-gray-700 dark:text-gray-300">
                <span>Passwort</span>
                <button
                  type="button"
                  className="text-xs text-primary"
                  onClick={() => setShowPassword((s) => !s)}
                >
                  {showPassword ? 'Verbergen' : 'Anzeigen'}
                </button>
              </div>
              <input
                autoComplete="current-password"
                type={showPassword ? 'text' : 'password'}
                className="w-full rounded border px-3 py-2 bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>

            {error ? (
              <div className="mt-3 text-sm text-red-600">{error}</div>
            ) : null}

            <div className="mt-6 flex items-center justify-between gap-3">
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-sky-600 text-white rounded disabled:opacity-60"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Lädt…' : 'Anmelden'}
              </button>
            </div>
          </form>

          <div className="mt-6 border-t border-gray-100 dark:border-slate-700 pt-4">
            {developmentLoginAvailable ? (
              <div className="text-sm">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-700 dark:text-gray-300">Development-Administrator</div>
                  <div>
                    <button
                      className="px-3 py-1 bg-amber-600 text-white rounded disabled:opacity-60"
                      onClick={handleDevLogin}
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? 'Lädt…' : 'Als Development-Administrator starten'}
                    </button>
                  </div>
                </div>
                <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                  Nur für die lokale Entwicklung. Dieser Zugang ist in Intranet- und Internet-Profilen nicht verfügbar.
                </div>
              </div>
            ) : null}
            {registrationAvailable ? (
              <div className="mt-4 text-sm">
                <button className="text-primary underline" onClick={() => onRegister?.()}>Noch kein Benutzerkonto? Registrieren</button>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
