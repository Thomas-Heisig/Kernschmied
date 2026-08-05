import React, { useEffect, useMemo, useState } from 'react';
import { useAuth } from './AuthProvider';
import { loadUserPreferences, updateUserPreferences } from './auth-api';
import type { UserPreferences, UpdateUserPreferencesInput } from './auth-contracts';
import { useTheme } from '../theme';

type LoadStatus = 'idle' | 'loading' | 'ready' | 'error';

export default function UserSettingsPanel() {
  const { user } = useAuth();
  const { theme: appliedTheme, setTheme } = useTheme();

  const [loadStatus, setLoadStatus] = useState<LoadStatus>('idle');
  const [prefsOriginal, setPrefsOriginal] = useState<UserPreferences | null>(null);
  const [language, setLanguage] = useState<string>('de');
  const [timezone, setTimezone] = useState<string>('Europe/Berlin');
  const [themeChoice, setThemeChoice] = useState<UserPreferences['theme']>('system');
  const [density, setDensity] = useState<UserPreferences['density']>('comfortable');
  const [defaultView, setDefaultView] = useState<string | null>(null);
  const [notificationsEnabled, setNotificationsEnabled] = useState<boolean>(true);

  const [isSaving, setIsSaving] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const previousAppliedTheme = useMemo(() => appliedTheme, []);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoadStatus('loading');
      setError(null);
      try {
        const p = await loadUserPreferences();
        if (!mounted) return;
        if (!p) throw new Error('Preferences not found');
        setPrefsOriginal(p);
        setLanguage(p.language ?? 'de');
        setTimezone(p.timezone ?? 'Europe/Berlin');
        setThemeChoice(p.theme ?? 'system');
        setDensity(p.density ?? 'comfortable');
        setDefaultView(p.defaultView ?? null);
        setNotificationsEnabled(Boolean(p.notificationsEnabled ?? true));
        setIsDirty(false);
        setLoadStatus('ready');
        // Apply theme choice immediately
        applyThemeChoice(p.theme ?? 'system');
      } catch (err: any) {
        setError(err?.message ?? String(err));
        setLoadStatus('error');
      }
    }

    void load();

    return () => {
      mounted = false;
      // on unmount, if dirty revert applied theme
      try {
        if (isDirty) {
          setTheme(previousAppliedTheme);
        }
      } catch {
        // ignore
      }
    };
  }, []);

  if (!user) return <div>Nicht angemeldet</div>;

  function applyThemeChoice(choice: UserPreferences['theme']) {
    try {
      if (choice === 'system') {
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        setTheme(prefersDark ? 'dark' : 'light');
      } else {
        setTheme(choice === 'dark' ? 'dark' : 'light');
      }
    } catch {
      // ignore
    }
  }

  function markDirty() {
    setIsDirty(true);
    setSuccessMessage(null);
    setError(null);
  }

  function handleThemeChange(v: UserPreferences['theme']) {
    setThemeChoice(v);
    applyThemeChoice(v);
    markDirty();
  }

  async function handleSave() {
    setIsSaving(true);
    setError(null);
    try {
      const input: UpdateUserPreferencesInput = {
        language,
        timezone,
        theme: themeChoice,
        density,
        defaultView,
        notificationsEnabled,
      };

      const updated = await updateUserPreferences(undefined, input);

      setPrefsOriginal(updated);
      setLanguage(updated.language);
      setTimezone(updated.timezone);
      setThemeChoice(updated.theme);
      setDensity(updated.density);
      setDefaultView(updated.defaultView ?? null);
      setNotificationsEnabled(Boolean(updated.notificationsEnabled));
      setIsDirty(false);
      setSuccessMessage('Einstellungen gespeichert');
      // ensure applied theme matches saved
      applyThemeChoice(updated.theme);
      window.setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: any) {
      // structured error handling for ApiError
      const message = err?.message ?? String(err);
      setError(message);
      // revert applied theme to previousAppliedTheme on error
      try {
        setTheme(previousAppliedTheme);
      } catch {
        // ignore
      }
    } finally {
      setIsSaving(false);
    }
  }

  function handleReset() {
    if (!prefsOriginal) return;
    setLanguage(prefsOriginal.language ?? 'de');
    setTimezone(prefsOriginal.timezone ?? 'Europe/Berlin');
    setThemeChoice(prefsOriginal.theme ?? 'system');
    setDensity(prefsOriginal.density ?? 'comfortable');
    setDefaultView(prefsOriginal.defaultView ?? null);
    setNotificationsEnabled(Boolean(prefsOriginal.notificationsEnabled));
    setIsDirty(false);
    setError(null);
    setSuccessMessage(null);
    applyThemeChoice(prefsOriginal.theme ?? 'system');
  }

  return (
    <div className="p-4 max-h-[80vh] overflow-auto">
      <h2 className="text-lg font-semibold">Persönliche Einstellungen</h2>

      {loadStatus === 'loading' && <div className="mt-2">Lade Einstellungen…</div>}
      {loadStatus === 'error' && <div className="mt-2 text-red-600">Fehler: {error}</div>}

      {loadStatus === 'ready' && (
        <>
          <div className="mt-4 space-y-4">
            <div>
              <label className="block text-sm mb-1">Sprache</label>
              <select value={language} onChange={(e) => { setLanguage(e.target.value); markDirty(); }} className="rounded border px-2 py-1 w-full max-w-xs">
                <option value="de">Deutsch</option>
                <option value="en">English</option>
              </select>
            </div>

            <div>
              <label className="block text-sm mb-1">Zeitzone</label>
              <select value={timezone} onChange={(e) => { setTimezone(e.target.value); markDirty(); }} className="rounded border px-2 py-1 w-full max-w-xs">
                <option value="Europe/Berlin">Europe/Berlin</option>
                <option value="UTC">UTC</option>
              </select>
            </div>

            <div>
              <label className="block text-sm mb-1">Theme</label>
              <select value={themeChoice} onChange={(e) => handleThemeChange(e.target.value as any)} className="rounded border px-2 py-1 w-full max-w-xs">
                <option value="system">System</option>
                <option value="light">Hell</option>
                <option value="dark">Dunkel</option>
              </select>
            </div>

            <div>
              <label className="block text-sm mb-1">Dichte</label>
              <select value={density} onChange={(e) => { setDensity(e.target.value as any); markDirty(); }} className="rounded border px-2 py-1 w-full max-w-xs">
                <option value="comfortable">Komfortabel</option>
                <option value="compact">Kompakt</option>
              </select>
            </div>

            <div>
              <label className="block text-sm mb-1">Standardansicht (optional)</label>
              <input value={defaultView ?? ''} onChange={(e) => { setDefaultView(e.target.value || null); markDirty(); }} placeholder="z.B. dashboard" className="rounded border px-2 py-1 w-full max-w-xs" />
            </div>

            <div className="flex items-center gap-2">
              <input id="notif" type="checkbox" checked={notificationsEnabled} onChange={(e) => { setNotificationsEnabled(e.target.checked); markDirty(); }} />
              <label htmlFor="notif" className="text-sm">Benachrichtigungen aktivieren</label>
            </div>
          </div>

          <div className="mt-6">
            <button disabled={!isDirty || isSaving} onClick={() => void handleSave()} className="px-3 py-1 bg-sky-600 text-white rounded">{isSaving ? 'Speichert…' : 'Speichern'}</button>
            <button disabled={isSaving} onClick={handleReset} className="ml-2 px-3 py-1 bg-slate-200 dark:bg-slate-700 rounded">Zurücksetzen</button>
          </div>

          {successMessage && <div className="mt-3 text-green-600">{successMessage}</div>}
          {error && <div className="mt-3 text-red-600">{error}</div>}
        </>
      )}
    </div>
  );
}
