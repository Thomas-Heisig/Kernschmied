import React, { useEffect, useState } from 'react';
import { loadSessions, revokeSession, logoutAllSessions } from './auth-api';
import type { UserSession } from './auth-contracts';
import { useAuth } from './AuthProvider';

function formatDate(ts: string | null) {
  if (!ts) return '—';
  try {
    const d = new Date(ts);
    return new Intl.DateTimeFormat('de-DE', { dateStyle: 'medium', timeStyle: 'short' }).format(d);
  } catch {
    return ts;
  }
}

function uaIcon(agent: string | null) {
  if (!agent) return '� device';
  if (agent.includes('Firefox')) return '🦊 Firefox';
  if (agent.includes('Chrome')) return '🌐 Chrome';
  if (agent.includes('Safari') && !agent.includes('Chrome')) return '🧭 Safari';
  if (agent.includes('Edg')) return '🔵 Edge';
  if (agent.includes('Windows')) return '🪟 Windows';
  if (agent.includes('Macintosh') || agent.includes('Mac OS')) return '🍎 macOS';
  if (agent.includes('Linux')) return '🐧 Linux';
  return '🌐 Browser';
}

export default function UserSessionsPanel({ onClose }: { onClose?: () => void }) {
  const { refreshCurrentUser, markUnauthenticated } = useAuth() as any;
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmLogoutAll, setConfirmLogoutAll] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await loadSessions();
      setSessions(res);
    } catch (err: any) {
      setError(err?.message ?? String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleRevoke(id: string, isCurrent: boolean) {
    try {
      await revokeSession(undefined, id);
      if (isCurrent) {
        markUnauthenticated();
      } else {
        await load();
      }
    } catch (err: any) {
      setError(err?.message ?? String(err));
    }
  }

  async function handleLogoutAll() {
    try {
      await logoutAllSessions();
      markUnauthenticated();
    } catch (err: any) {
      setError(err?.message ?? String(err));
    } finally {
      setConfirmLogoutAll(false);
    }
  }

  return (
    <div>
      <h2 className="text-lg font-semibold">Sitzungen</h2>

      {loading && <div>Lade Sitzungen…</div>}
      {error && <div className="text-red-600">{error}</div>}

      <div className="mt-4 space-y-3 text-sm">
        {sessions.map((s) => (
          <div key={s.id} className="p-3 border rounded">
            <div className="flex justify-between">
              <div>
                <div className="font-medium">{uaIcon(s.userAgent)} — {s.authenticationMethod || 'Session'}</div>
                <div className="text-xs text-gray-600">Erstellt: {formatDate(s.createdAt)}</div>
                <div className="text-xs text-gray-600">Zuletzt aktiv: {formatDate(s.lastSeenAt)}</div>
                <div className="text-xs text-gray-600">IP: {s.ipAddress ?? '—'}</div>
                <div className="text-xs text-gray-600">Agent: {s.userAgent ?? '—'}</div>
              </div>
              <div className="flex flex-col items-end space-y-2">
                <div className="text-xs font-medium text-sky-700">{s.current ? 'Aktuelle Sitzung' : ''}</div>
                <button type="button" aria-label={s.current ? 'Aktuelle Sitzung widerrufen' : 'Sitzung widerrufen'} onClick={() => handleRevoke(s.id, !!s.current)} className="px-3 py-1 bg-red-600 text-white rounded text-sm">Widerrufen</button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4">
        { !confirmLogoutAll ? (
          <button type="button" onClick={() => setConfirmLogoutAll(true)} className="px-3 py-1 bg-red-700 text-white rounded">Alle Sitzungen abmelden</button>
        ) : (
          <div className="inline-flex items-center gap-2">
            <span className="text-sm">Wirklich alle Sitzungen abmelden?</span>
            <button type="button" onClick={() => void handleLogoutAll()} className="px-3 py-1 bg-red-700 text-white rounded">Ja, abmelden</button>
            <button type="button" onClick={() => setConfirmLogoutAll(false)} className="px-3 py-1 bg-slate-200 rounded">Abbrechen</button>
          </div>
        )}

        <button type="button" onClick={() => onClose && onClose()} className="ml-2 px-3 py-1 bg-slate-200 rounded">Schließen</button>
      </div>
    </div>
  );
}
