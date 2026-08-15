// F:\Kernschmied\frontend\src\components\settings\SettingsSidebar.tsx

import { useMemo } from 'react';

import type { ConfigObject, ConfigGroupResponse } from '../../contracts/config';
import IconBadge from '../common/IconBadge';

interface SettingsSidebarProps {
  values: ConfigObject;
  groups?: ConfigGroupResponse[] | null;
  activeKey: string | null;
  isJsonActive: boolean;
  onSelectKey: (key: string | null) => void;
  onSelectJson: () => void;
}

const SETTINGS_CATALOG_KEY = 'settings-catalog';

export function SettingsSidebar({
  values,
  groups,
  activeKey,
  isJsonActive,
  onSelectKey,
  onSelectJson,
}: SettingsSidebarProps) {
  const sections = useMemo<string[]>(() => {
    if (groups && Array.isArray(groups) && groups.length > 0) {
      return groups
        .map((g: ConfigGroupResponse) => g.id)
        .sort((left: string, right: string) =>
          formatSidebarLabel(left).localeCompare(formatSidebarLabel(right), 'de', { sensitivity: 'base' }),
        );
    }

    return Object.keys(values).sort((left: string, right: string) =>
      formatSidebarLabel(left).localeCompare(formatSidebarLabel(right), 'de', { sensitivity: 'base' }),
    );
  }, [values, groups]);

  const isCatalogActive = activeKey === SETTINGS_CATALOG_KEY && !isJsonActive;

  const isAllSettingsActive = activeKey === null && !isJsonActive;

  return (
    <nav
      className={[
        'flex w-64 shrink-0 flex-col overflow-y-auto',
        'border-r border-slate-200 bg-slate-50/80',
        'dark:border-white/10 dark:bg-slate-950/50',
      ].join(' ')}
      aria-label="Einstellungskategorien"
    >
      <div className="flex min-h-full flex-col p-3">
        <SidebarSectionLabel>Übersicht</SidebarSectionLabel>

        <div className="space-y-1">
          <button
            type="button"
            className={sidebarItemClass(isCatalogActive)}
            aria-current={isCatalogActive ? 'page' : undefined}
            onClick={() => {
              onSelectKey(SETTINGS_CATALOG_KEY);
            }}
          >
            <SidebarIcon>
              <CatalogIcon />
            </SidebarIcon>

            <span className="min-w-0 flex-1">
              <span className="block truncate">Settings-Katalog</span>

              <span className="mt-0.5 block truncate text-xs opacity-70">
                Werte, Ressourcen und Laufzeitbereiche
              </span>
            </span>
          </button>

          <button
            type="button"
            className={sidebarItemClass(isAllSettingsActive)}
            aria-current={isAllSettingsActive ? 'page' : undefined}
            onClick={() => {
              onSelectKey(null);
            }}
          >
            <SidebarIcon>
              <OverviewIcon />
            </SidebarIcon>

            <span className="min-w-0 flex-1">
              <span className="block truncate">Alle Einstellungen</span>

              <span className="mt-0.5 block truncate text-xs opacity-70">
                Aktuelle Konfigurationswerte
              </span>
            </span>
          </button>
        </div>

        <SidebarDivider />

        <SidebarSectionLabel>Konfiguration</SidebarSectionLabel>

        <div className="space-y-1">
          {sections.length > 0 ? (
            sections.map((key: string) => {
              const isActive = activeKey === key && !isJsonActive;

              return (
                <div key={key}>
                  <button
                    type="button"
                    className={sidebarItemClass(isActive)}
                    aria-current={isActive ? 'page' : undefined}
                    title={formatSidebarLabel(key)}
                    onClick={() => {
                      onSelectKey(key);
                    }}
                  >
                    <SidebarIcon>
                      <SectionIcon />
                    </SidebarIcon>

                    <span className="min-w-0 flex-1 truncate">{formatSidebarLabel(key)}</span>

                    <span
                      className={[
                        'ml-2 shrink-0 rounded-full px-2 py-0.5',
                        'text-[11px] font-medium',
                        isActive
                          ? 'bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200'
                          : 'bg-slate-200/70 text-slate-500 dark:bg-white/5 dark:text-slate-400',
                      ].join(' ')}
                    >
                      {groups && Array.isArray(groups)
                        ? (groups.find((g: ConfigGroupResponse) => g.id === key)?.entries ?? []).length
                        : countSectionEntries(values[key])}
                    </span>
                  </button>

                  {/** Expand the active group to list sections and fields so specific settings
                   * can be selected directly from the sidebar. We consider the group active
                   * when the current activeKey equals the group id or starts with "group." */}
                  {isActive && groups && Array.isArray(groups) ? (
                    <div className="pl-6 mt-2 space-y-2">
                      {(() => {
                        const group = groups.find((g: ConfigGroupResponse) => g.id === key) as any;
                        return group?.sections?.map((section: any) => (
                          <div key={section.id} className="space-y-1">
                            <div className="text-xs text-slate-500">{section.title}</div>
                            <div className="mt-1 space-y-1">
                              {section.fields.map((field: any) => {
                                const cfgGroup = field.config_group ?? key;
                                const cfgKey = field.config_key ?? field.id;
                                const fullKey = `${cfgGroup.trim()}.${cfgKey.trim()}`;
                                const isFieldActive = activeKey === fullKey;

                                return (
                                  <button
                                    key={field.id}
                                    type="button"
                                    className={[
                                      'w-full text-left rounded px-2 py-1 text-sm',
                                      isFieldActive
                                        ? 'bg-white text-slate-900 font-medium'
                                        : 'text-slate-600 hover:bg-white/70',
                                    ].join(' ')}
                                    aria-current={isFieldActive ? 'true' : undefined}
                                      onClick={() => {
                                        console.debug("[SettingsSidebar] select", fullKey);
                                        onSelectKey(fullKey);
                                      }}
                                  >
                                    {field.title}
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        ));
                      })()}
                    </div>
                  ) : null}
                </div>
              );
            })
          ) : (
            <div className="rounded-lg border border-dashed border-slate-300 px-3 py-4 text-center dark:border-white/10">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Keine Konfigurationsbereiche vorhanden.
              </p>
            </div>
          )}
        </div>

        <div className="mt-auto pt-4">
          <SidebarDivider />

          <SidebarSectionLabel>Erweitert</SidebarSectionLabel>

          <button
            type="button"
            className={sidebarItemClass(isJsonActive)}
            aria-current={isJsonActive ? 'page' : undefined}
            onClick={onSelectJson}
          >
            <SidebarIcon>
              <JsonIcon />
            </SidebarIcon>

            <span className="min-w-0 flex-1">
              <span className="block truncate">JSON-Editor</span>

              <span className="mt-0.5 block truncate text-xs opacity-70">
                Gesamte Konfiguration bearbeiten
              </span>
            </span>
          </button>
        </div>
      </div>
    </nav>
  );
}

function SidebarSectionLabel({ children }: { children: string }) {
  return (
    <p
      className={[
        'mb-2 px-3 text-[11px] font-semibold uppercase',
        'tracking-[0.12em] text-slate-400',
        'dark:text-slate-500',
      ].join(' ')}
    >
      {children}
    </p>
  );
}

function SidebarDivider() {
  return <hr className="my-3 border-slate-200 dark:border-white/10" />;
}

function SidebarIcon({ children }: { children: React.ReactNode }) {
  return (
    <div aria-hidden="true">
      <IconBadge icon={children as React.ReactNode} size="sm" variant="secondary" />
    </div>
  );
}

function sidebarItemClass(isActive: boolean): string {
  return [
    'group flex w-full items-center rounded-xl px-2.5 py-2.5',
    'text-left text-sm font-normal transition',
    'focus-visible:outline-none focus-visible:ring-2',
    'focus-visible:ring-blue-500 focus-visible:ring-offset-2',
    'dark:focus-visible:ring-offset-slate-950',
    isActive
      ? [
          'bg-white text-slate-950 shadow-sm',
          'ring-1 ring-slate-200',
          'dark:bg-slate-800 dark:text-white',
          'dark:ring-white/10',
        ].join(' ')
      : [
          'text-slate-600',
          'hover:bg-white/70 hover:text-slate-950',
          'dark:text-slate-400',
          'dark:hover:bg-slate-800/70',
          'dark:hover:text-white',
        ].join(' '),
  ].join(' ');
}

function countSectionEntries(value: ConfigObject[string] | undefined): number {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return value === undefined ? 0 : 1;
  }

  return Object.keys(value).length;
}

function formatSidebarLabel(key: string): string {
  return key.replace(/[_-]+/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase());
}

function CatalogIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3" y="3" width="7" height="7" rx="1.5" />

      <rect x="14" y="3" width="7" height="7" rx="1.5" />

      <rect x="3" y="14" width="7" height="7" rx="1.5" />

      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </svg>
  );
}

function OverviewIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M4 6h16" />
      <path d="M4 12h16" />
      <path d="M4 18h16" />
    </svg>
  );
}

function SectionIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M4 5h16" />
      <path d="M4 12h10" />
      <path d="M4 19h13" />
    </svg>
  );
}

function JsonIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M8 3H6a2 2 0 0 0-2 2v4a2 2 0 0 1-2 2 2 2 0 0 1 2 2v4a2 2 0 0 0 2 2h2" />
      <path d="M16 3h2a2 2 0 0 1 2 2v4a2 2 0 0 0 2 2 2 2 0 0 0-2 2v4a2 2 0 0 1-2 2h-2" />
    </svg>
  );
}
