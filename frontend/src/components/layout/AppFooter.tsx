// F:\Kernschmied\frontend\src\components\layout\AppFooter.tsx

import { useEffect, useMemo, useState } from "react";
import {
  CalendarDays,
  Database,
  FolderTree,
  Plug,
  Server,
  Wifi,
} from "lucide-react";

interface AppFooterProps {
  schemaVersion?: string;

  environment?: string;

  apiVersion?: string;

  applicationVersion?: string;

  configRevision?: number;

  modelRevision?: number;

  toolRevision?: number;

  backendOnline?: boolean;
}

export function AppFooter({
  schemaVersion,
  environment = "Development",
  apiVersion = "v1",
  applicationVersion = "0.1.0",
  configRevision = 1,
  modelRevision = 1,
  toolRevision = 1,
  backendOnline = true,
}: AppFooterProps) {
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const timer = window.setInterval(() => {
      setNow(new Date());
    }, 1000);

    return () => window.clearInterval(timer);
  }, []);

  const formattedDate = useMemo(
    () =>
      new Intl.DateTimeFormat("de-DE", {
        weekday: "short",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      }).format(now),
    [now],
  );

  return (
    <footer className="z-30 shrink-0 border-t border-border bg-white/90 backdrop-blur-md dark:border-white/10 dark:bg-slate-950/90">
      <div className="flex h-10 items-center justify-between gap-6 overflow-x-auto px-4 text-xs text-text-muted dark:text-gray-400">
        {/* Linke Seite */}

        <div className="flex shrink-0 items-center gap-5">
          <StatusItem>
            <strong className="font-semibold text-text dark:text-white">
              Kernschmied {applicationVersion}
            </strong>
          </StatusItem>

          <StatusItem>{environment}</StatusItem>

          <StatusItem icon={<Server size={14} />}>API {apiVersion}</StatusItem>

          {schemaVersion && (
            <StatusItem icon={<FolderTree size={14} />}>
              Schema {schemaVersion}
            </StatusItem>
          )}
        </div>

        {/* Mitte */}

        <div className="flex shrink-0 items-center gap-5">
          <StatusItem icon={<Database size={14} />}>
            Config {configRevision}
          </StatusItem>

          <StatusItem icon={<Database size={14} />}>
            Models {modelRevision}
          </StatusItem>

          <StatusItem icon={<Plug size={14} />}>
            Tools {toolRevision}
          </StatusItem>

          <StatusItem icon={<Wifi size={14} />}>
            <span
              className={
                backendOnline
                  ? "text-emerald-600 dark:text-emerald-400"
                  : "text-red-500"
              }
            >
              ●
            </span>

            {backendOnline ? " Backend online" : " Backend offline"}
          </StatusItem>
        </div>

        {/* Rechte Seite */}

        <div className="flex shrink-0 items-center gap-2 font-medium">
          <CalendarDays
            size={14}
            className="text-text-muted dark:text-gray-400"
          />

          <span>{formattedDate}</span>
        </div>
      </div>
    </footer>
  );
}

interface StatusItemProps {
  children: React.ReactNode;

  icon?: React.ReactNode;
}

function StatusItem({ children, icon }: StatusItemProps) {
  return (
    <div className="flex items-center gap-1.5 whitespace-nowrap">
      {icon}

      <span>{children}</span>
    </div>
  );
}
