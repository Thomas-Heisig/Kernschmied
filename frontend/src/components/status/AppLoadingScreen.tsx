// F:\Kernschmied\frontend\src\components\status\AppLoadingScreen.tsx

export function AppLoadingScreen() {
  return (
    <main
      className="flex h-full min-h-0 items-center justify-center bg-surface-muted p-6 dark:bg-slate-900/30"
      aria-busy="true"
      aria-live="polite"
      aria-label="Anwendung wird geladen"
    >
      <section className="animate-fade-in rounded-2xl border border-border-soft bg-white/80 px-6 py-5 shadow-glass backdrop-blur-md dark:border-white/10 dark:bg-slate-800/80">
        <div className="flex items-center gap-3">
          <div
            className="h-5 w-5 animate-pulse rounded-full bg-primary/60 dark:bg-primary/40"
            aria-hidden="true"
          />

          <p className="text-sm font-medium text-text-soft dark:text-gray-300">
            Kernschmied wird geladen …
          </p>
        </div>
      </section>
    </main>
  );
}
