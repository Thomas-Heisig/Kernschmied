// F:\Kernschmied\frontend\src\components\layout\AppHeader.tsx

import { useEffect, useState } from 'react';

import {
  BookOpen,
  CircleUserRound,
  Globe2,
  Moon,
  Settings,
  ShieldCheck,
  Sun,
  CalendarDays,
  Bell,
} from 'lucide-react';
import IconBadge from '../common/IconBadge';
import UserMenu from '../../auth/UserMenu';
import { useAuth } from '../../auth/AuthProvider';
import { loadMyMentions } from '../../api/mentions';
import { loadUserPreferences } from '../../auth/auth-api';

type AppTheme = 'light' | 'dark';

interface AppHeaderProps {
  theme: AppTheme;
  schemaVersion?: string;
  applicationVersion?: string;
  environment?: string;
  userName?: string;
  onToggleTheme: () => void;
  onOpenSettings: () => void;
  onOpenDocumentation: () => void;
  onOpenCalendar?: () => void;
  onCreatePublicWorkspace?: () => void;
  onCreateInternWorkspace?: () => void;
}

export function AppHeader({
  theme,
  schemaVersion,
  applicationVersion = '0.1.0',
  environment = 'Development',
  userName = 'Thomas Heisig',
  onToggleTheme,
  onOpenSettings,
  onOpenDocumentation,
  onOpenCalendar,
  onCreatePublicWorkspace,
  onCreateInternWorkspace,
}: AppHeaderProps) {
  const auth = useAuth();
  const [unreadMentionCount, setUnreadMentionCount] = useState(0);
  const [notificationSoundEnabled, setNotificationSoundEnabled] = useState(false);
  const resolvedUserName = auth?.user?.displayName ?? userName;
  const userInitials = createInitials(resolvedUserName);
  const normalizedEnvironment = environment.trim().toLowerCase();
  const environmentLabel =
    normalizedEnvironment === 'development'
      ? 'Entwicklung'
      : normalizedEnvironment === 'intranet'
        ? 'Intranet'
        : normalizedEnvironment === 'internet'
          ? 'Internet'
          : environment;

  const themeLabel =
    theme === 'dark' ? 'Helles Farbschema aktivieren' : 'Dunkles Farbschema aktivieren';

  const actionButtonClassName =
    'inline-flex h-9 w-9 items-center justify-center rounded-lg text-text-soft transition-colors hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 dark:text-gray-300 dark:hover:bg-slate-800 dark:hover:text-white dark:focus-visible:ring-offset-slate-950';

  useEffect(() => {
    if (!auth?.user) {
      setUnreadMentionCount(0);
      return;
    }
    let active = true;
    const refresh = () => {
      void Promise.all([loadMyMentions(), loadUserPreferences()])
        .then(([mentions, preferences]) => {
          if (active) {
            const nextCount = mentions.filter((mention) => mention.status === 'unread').length;
            const soundEnabled = Boolean(preferences?.notificationSoundEnabled);
            setNotificationSoundEnabled(soundEnabled);
            setUnreadMentionCount((currentCount) => {
              if (soundEnabled && nextCount > currentCount && currentCount >= 0) {
                const audioContext = new AudioContext();
                const oscillator = audioContext.createOscillator();
                const gain = audioContext.createGain();
                oscillator.frequency.value = 740;
                gain.gain.value = 0.04;
                oscillator.connect(gain).connect(audioContext.destination);
                oscillator.start();
                oscillator.stop(audioContext.currentTime + 0.12);
              }
              return nextCount;
            });
          }
        })
        .catch(() => undefined);
    };
    refresh();
    const interval = window.setInterval(refresh, 30_000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, [auth?.user?.id]);

  return (
    <header className="relative z-30 shrink-0 border-b border-border bg-white/90 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-slate-950/90">
      <div className="flex h-16 min-w-0 items-center justify-between gap-4 px-4 sm:px-6">
        {/* Logo & Titel */}
        <div className="flex min-w-0 items-center gap-3">
          <div className="relative shrink-0">
            <IconBadge
              icon={<img src="/favicon.png" alt="Kernschmied" className="h-8 w-8 object-contain" />}
              size="lg"
              variant="primary"
            />
            <span
              className="absolute -right-1 -bottom-1 h-3 w-3 rounded-full border-2 border-white bg-emerald-500 dark:border-slate-950"
              title="Anwendung bereit"
              aria-label="Anwendung bereit"
            />
          </div>

          <div className="min-w-0">
            <div className="flex min-w-0 items-center gap-2">
              <h1 className="truncate text-base font-semibold tracking-tight text-text dark:text-white">
                Kernschmied
              </h1>
              <span className="hidden shrink-0 rounded-md border border-border-soft bg-surface-muted px-1.5 py-0.5 font-mono text-[10px] font-medium text-text-muted dark:border-white/10 dark:bg-slate-800 dark:text-gray-400 sm:inline">
                v{applicationVersion}
              </span>
            </div>

            <div className="mt-0.5 flex min-w-0 items-center gap-2 text-xs text-text-muted dark:text-gray-400">
              <span className="truncate">Modulare Chat-Anwendung</span>
              {schemaVersion ? (
                <>
                  <span
                    className="hidden text-border dark:text-gray-600 sm:inline"
                    aria-hidden="true"
                  >
                    •
                  </span>
                  <span className="hidden shrink-0 sm:inline">
                    UI-Schema <code className="font-mono text-primary">{schemaVersion}</code>
                  </span>
                </>
              ) : null}
            </div>
          </div>
        </div>

        {/* Rechte Seite: Aktionen & Benutzer */}
        <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
          {/* Environment-Badge */}
          <div
            className="hidden items-center gap-1.5 rounded-lg border border-border-soft bg-surface-muted/80 px-2.5 py-1.5 text-xs font-medium text-text-soft dark:border-white/10 dark:bg-slate-800/70 dark:text-gray-300 md:flex"
            title={`Betriebsprofil: ${environmentLabel}`}
          >
            <IconBadge
              icon={<ShieldCheck className="text-emerald-600 dark:text-emerald-400" />}
              size="sm"
              variant="default"
            />
            <span>{environmentLabel}</span>
          </div>

          <div className="hidden h-7 w-px bg-border dark:bg-white/10 sm:block" />

          {/* UserMenu (Desktop) */}
          <div className="hidden sm:flex">
            <UserMenu />
          </div>

          {/* Aktionen */}
          <button
            type="button"
            onClick={() => window.dispatchEvent(new Event('kernschmied:open-context'))}
            className={`${actionButtonClassName} relative`}
            aria-label={`${unreadMentionCount} offene Anfragen`}
            title="Anfragen und Online-Benutzer anzeigen"
          >
            <IconBadge
              icon={<Bell />}
              size="sm"
              variant="default"
              className={unreadMentionCount >= 5 ? 'text-danger' : unreadMentionCount > 0 ? 'text-primary' : 'text-emerald-600'}
            />
            {unreadMentionCount > 0 ? (
              <span className="absolute -right-1 -top-1 min-w-4 rounded-full bg-danger px-1 text-center text-[10px] font-bold leading-4 text-white">
                {unreadMentionCount > 99 ? '99+' : unreadMentionCount}
              </span>
            ) : null}
          </button>

          <button
            type="button"
            onClick={onOpenDocumentation}
            className={actionButtonClassName}
            aria-label="Dokumentation öffnen"
            title="Dokumentation und Benutzerhandbuch öffnen"
          >
            <IconBadge icon={<BookOpen />} size="sm" variant="default" />
          </button>

          <button
            type="button"
            onClick={onOpenCalendar}
            className={actionButtonClassName}
            aria-label="Kalender verwalten"
            title="Kalenderverwaltung öffnen"
          >
            <IconBadge icon={<CalendarDays />} size="sm" variant="default" />
          </button>

          <button
            type="button"
            onClick={onOpenSettings}
            className={actionButtonClassName}
            aria-label="Einstellungen öffnen"
            title="Einstellungen öffnen"
          >
            <IconBadge icon={<Settings />} size="sm" variant="default" />
          </button>

          <button
            type="button"
            onClick={onToggleTheme}
            className={actionButtonClassName}
            aria-label={themeLabel}
            title={themeLabel}
            aria-pressed={theme === 'dark'}
          >
            <IconBadge
              icon={theme === 'dark' ? <Sun /> : <Moon />}
              size="sm"
              variant={theme === 'dark' ? 'primary' : 'default'}
            />
          </button>

          {/* Mobile Benutzer-Avatar (mit Initialen) */}
          <div className="flex h-9 w-9 items-center justify-center sm:hidden">
            <IconBadge
              icon={<span className="text-xs font-bold uppercase">{userInitials}</span>}
              size="md"
              variant="secondary"
              aria-label={`Angemeldet als ${resolvedUserName}`}
            />
          </div>
        </div>
      </div>
    </header>
  );
}

function createInitials(name: string): string {
  const normalizedName = name.trim();

  if (!normalizedName) {
    return '?';
  }

  const nameParts = normalizedName.split(/\s+/).filter((part) => part.length > 0);

  if (nameParts.length === 1) {
    return nameParts[0].slice(0, 2).toUpperCase();
  }

  const firstInitial = nameParts[0].charAt(0);
  const lastInitial = nameParts[nameParts.length - 1].charAt(0);

  return `${firstInitial}${lastInitial}`.toUpperCase();
}