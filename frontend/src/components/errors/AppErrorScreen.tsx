// F:\Kernschmied\frontend\src\components\errors\AppErrorScreen.tsx

import IconBadge from '../common/IconBadge';

interface AppErrorScreenProps {
  message: string;
  requestId?: string;
  onRetry: () => void;
}

function ErrorIcon() {
  return (
    <svg
      className="h-6 w-6"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path d="M12 9v4" strokeLinecap="round" strokeWidth="1.8" />
      <path d="M12 17h.01" strokeLinecap="round" strokeWidth="2.4" />
      <path
        d="M10.29 3.86 2.82 17a2 2 0 0 0 1.74 3h14.88a2 2 0 0 0 1.74-3L13.71 3.86a2 2 0 0 0-3.42 0Z"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

export function AppErrorScreen({ message, requestId, onRetry }: AppErrorScreenProps) {
  return (
    <main className="flex h-full min-h-0 items-center justify-center overflow-y-auto bg-surface-muted p-6 dark:bg-slate-900/30">
      <section
        className="w-full max-w-lg animate-fade-in rounded-2xl border border-danger/30 bg-white/80 p-6 shadow-glass backdrop-blur-md dark:border-danger/20 dark:bg-slate-800/80"
        role="alert"
        aria-live="assertive"
      >
        <div className="flex items-start gap-4">
          <div aria-hidden="true">
            <IconBadge icon={<ErrorIcon />} size="lg" variant="danger" />
          </div>

          <div className="min-w-0 flex-1">
            <h1 className="text-lg font-semibold text-danger">Anwendung konnte nicht geladen werden</h1>
            <p className="mt-3 text-sm leading-6 text-text-soft dark:text-gray-300">{message}</p>
            {requestId && (
              <p className="mt-3 break-all text-xs text-text-muted dark:text-gray-500">
                Anfrage-ID: <code className="font-mono">{requestId}</code>
              </p>
            )}
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            type="button"
            className="inline-flex items-center rounded-xl bg-primary px-4 py-2 text-sm font-medium text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 dark:bg-primary/80 dark:hover:bg-primary"
            onClick={onRetry}
          >
            Erneut versuchen
          </button>
        </div>
      </section>
    </main>
  );
}