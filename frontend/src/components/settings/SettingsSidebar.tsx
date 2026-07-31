// F:\Kernschmied\frontend\src\components\settings\SettingsSidebar.tsx

import type { ConfigObject } from "../../contracts/config";

interface SettingsSidebarProps {
  values: ConfigObject;
  activeKey: string | null;
  isJsonActive: boolean;
  onSelectKey: (key: string | null) => void;
  onSelectJson: () => void;
}

export function SettingsSidebar({
  values,
  activeKey,
  isJsonActive,
  onSelectKey,
  onSelectJson,
}: SettingsSidebarProps) {
  const sections = Object.keys(values).sort();

  return (
    <nav
      className="flex w-56 shrink-0 flex-col overflow-y-auto border-r border-slate-200 bg-slate-50/80 dark:border-white/10 dark:bg-slate-950/50"
      aria-label="Einstellungskategorien"
    >
      <div className="p-3">
        <button
          type="button"
          className={sidebarItemClass(activeKey === null && !isJsonActive)}
          onClick={() => onSelectKey(null)}
        >
          <span className="truncate">Alle Einstellungen</span>
        </button>

        {sections.map((key) => (
          <button
            key={key}
            type="button"
            className={sidebarItemClass(activeKey === key && !isJsonActive)}
            onClick={() => onSelectKey(key)}
          >
            <span className="truncate">{formatSidebarLabel(key)}</span>
          </button>
        ))}

        <hr className="my-2 border-slate-200 dark:border-white/10" />

        <button
          type="button"
          className={sidebarItemClass(isJsonActive)}
          onClick={onSelectJson}
        >
          <span className="truncate">JSON-Editor</span>
        </button>
      </div>
    </nav>
  );
}

function sidebarItemClass(isActive: boolean): string {
  return [
    "flex w-full items-center rounded-lg px-3 py-2 text-left text-sm font-normal transition",
    isActive
      ? "bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white"
      : "text-slate-600 hover:bg-white/60 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/60 dark:hover:text-white",
  ].join(" ");
}

function formatSidebarLabel(key: string): string {
  return key.replace(/[_-]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
