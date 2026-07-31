import type { ReactNode } from "react";

import { AppFooter } from "./AppFooter";
import { AppHeader } from "./AppHeader";

interface AppLayoutProps {
  children: ReactNode;
  hierarchySidebar: ReactNode;
  contextSidebar: ReactNode;

  theme: "light" | "dark";

  schemaVersion?: string;
  applicationVersion?: string;
  environment?: string;
  userName?: string;

  onToggleTheme: () => void;
  onOpenSettings: () => void;
}

export function AppLayout({
  children,
  hierarchySidebar,
  contextSidebar,
  theme,
  schemaVersion,
  applicationVersion,
  environment,
  userName,
  onToggleTheme,
  onOpenSettings,
}: AppLayoutProps) {
  return (
    <div className="flex h-full min-h-0 w-full flex-col overflow-hidden bg-surface-muted text-text dark:bg-slate-950 dark:text-white">
      <AppHeader
        theme={theme}
        schemaVersion={schemaVersion}
        applicationVersion={applicationVersion}
        environment={environment}
        userName={userName}
        onToggleTheme={onToggleTheme}
        onOpenSettings={onOpenSettings}
      />

      <div className="flex min-h-0 min-w-0 flex-1 overflow-hidden">
        {hierarchySidebar}

        <main
          className="flex min-h-0 min-w-0 flex-1 overflow-hidden"
          aria-label="Anwendungsbereich"
        >
          {children}
        </main>

        {contextSidebar}
      </div>

      <AppFooter schemaVersion={schemaVersion} />
    </div>
  );
}
