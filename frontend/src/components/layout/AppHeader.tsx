// F:\Kernschmied\frontend\src\components\layout\AppHeader.tsx

import {
  BookOpen,
  CircleUserRound,
  Globe2,
  Moon,
  Settings,
  ShieldCheck,
  Sun,
  CalendarDays,
} from 'lucide-react';
import UserMenu from '../../auth/UserMenu';
import { useAuth } from '../../auth/AuthProvider';

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

  return (
    <header className="relative z-30 shrink-0 border-b border-border bg-white/90 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-slate-950/90">
      <div className="flex h-16 min-w-0 items-center justify-between gap-4 px-4 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <div className="relative shrink-0">
            <div className="flex h-10 w-10 items-center justify-center overflow-hidden rounded-xl border border-border-soft bg-white shadow-sm dark:border-white/10 dark:bg-slate-800">
              <img src="/favicon.png" alt="Kernschmied" className="h-8 w-8 object-contain" />
            </div>
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
                    className="hidden text-border sm:inline dark:text-gray-600"
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

          <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
          {/* Public/Intern workspace creation buttons removed from header */}
          <div
            className="hidden items-center gap-1.5 rounded-lg border border-border-soft bg-surface-muted/80 px-2.5 py-1.5 text-xs font-medium text-text-soft dark:border-white/10 dark:bg-slate-800/70 dark:text-gray-300 md:flex"
            title={`Betriebsprofil: ${environmentLabel}`}
          >
            <ShieldCheck
              size={14}
              className="text-emerald-600 dark:text-emerald-400"
              aria-hidden="true"
            />
            <span>{environmentLabel}</span>
          </div>

          <div className="hidden h-7 w-px bg-border dark:bg-white/10 sm:block" />

          <div className="hidden sm:flex">
            <UserMenu />
          </div>

          <button
            type="button"
            onClick={onOpenDocumentation}
            className={actionButtonClassName}
            aria-label="Dokumentation öffnen"
            title="Dokumentation und Benutzerhandbuch öffnen"
          >
            <BookOpen size={18} aria-hidden="true" />
          </button>

          <button
            type="button"
            onClick={onOpenCalendar}
            className={actionButtonClassName}
            aria-label="Kalender verwalten"
            title="Kalenderverwaltung öffnen"
          >
            <CalendarDays size={18} aria-hidden="true" />
          </button>

          <button
            type="button"
            onClick={onOpenSettings}
            className={actionButtonClassName}
            aria-label="Einstellungen öffnen"
            title="Einstellungen öffnen"
          >
            <Settings size={18} aria-hidden="true" />
          </button>

          <button
            type="button"
            onClick={onToggleTheme}
            className={actionButtonClassName}
            aria-label={themeLabel}
            title={themeLabel}
            aria-pressed={theme === 'dark'}
          >
            {theme === 'dark' ? (
              <Sun size={18} aria-hidden="true" />
            ) : (
              <Moon size={18} aria-hidden="true" />
            )}
          </button>

          <div className="flex h-9 w-9 items-center justify-center sm:hidden">
            <CircleUserRound
              size={20}
              className="text-text-soft dark:text-gray-300"
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
