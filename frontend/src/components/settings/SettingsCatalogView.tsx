// F:\Kernschmied\frontend\src\components\settings\SettingsCatalogView.tsx

import { useCallback, useEffect, useMemo, useState } from 'react';

import type { ReactNode } from 'react';

import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Database,
  ExternalLink,
  RefreshCw,
  Search,
  Settings2,
  ShieldAlert,
  Wrench,
  X,
} from 'lucide-react';

import { fetchSettingsCatalog } from '../../api/settingsCatalog';
import type { ConfigObject, ConfigValue, ConfigEntryResponse, ConfigUIComponent } from '../../contracts/config';
import type {
  SettingsAvailability,
  SettingsCatalogResponse,
  SettingsFieldDescriptor,
  SettingsGroupDescriptor,
  SettingsSectionDescriptor,
} from '../../contracts/settings';
import type { UseSystemConfigReturn } from '../../hooks/useSystemConfig';
import { SettingsField } from './SettingsField';

const DEFAULT_GROUP_ID = 'identity';

const badgeLabel: Record<SettingsAvailability, string> = {
  available: 'Erreichbar',
  prepared: 'Vorbereitet',
  planned: 'Geplant',
};

const sourceLabel: Record<string, string> = {
  config: 'Konfiguration',
  resource: 'Verwaltete Ressource',
  runtime: 'Laufzeitstatus',
  local_preference: 'Lokale Benutzerpräferenz',
};

const controlLabel: Record<string, string> = {
  text: 'Textfeld',
  textarea: 'Mehrzeiliger Text',
  number: 'Zahlenfeld',
  boolean: 'Schalter',
  select: 'Auswahl',
  multiselect: 'Mehrfachauswahl',
  readonly: 'Nur Anzeige',
  link: 'Ressourcenansicht',
};

interface SettingsCatalogViewProps {
  config: UseSystemConfigReturn;
}

interface FilteredGroup {
  group: SettingsGroupDescriptor;
  sections: SettingsSectionDescriptor[];
}

interface GroupPanelProps {
  group: SettingsGroupDescriptor;
  sections: SettingsSectionDescriptor[];
  config: UseSystemConfigReturn;
  valuesByFullKey?: Record<string, ConfigValue> | null;
}

interface SectionPanelProps {
  section: SettingsSectionDescriptor;
  config: UseSystemConfigReturn;
  valuesByFullKey?: Record<string, ConfigValue> | null;
}

interface FieldCardProps {
  field: SettingsFieldDescriptor;
  config: UseSystemConfigReturn;
  valuesByFullKey?: Record<string, ConfigValue> | null;
}

// ============================================================
// Type Guard für editierbare Config-Felder
// ============================================================

interface EditableConfigFieldDescriptor extends SettingsFieldDescriptor {
  source: 'config';
  editable: true;
  config_group: string;
  config_key: string;
}

function isEditableConfigField(
  field: SettingsFieldDescriptor,
): field is EditableConfigFieldDescriptor {
  return (
    field.source === 'config' &&
    field.editable === true &&
    typeof field.config_group === 'string' &&
    field.config_group.trim().length > 0 &&
    typeof field.config_key === 'string' &&
    field.config_key.trim().length > 0
  );
}

// ============================================================
// Hauptkomponente
// ============================================================

export function SettingsCatalogView({ config }: SettingsCatalogViewProps) {
  const [catalog, setCatalog] = useState<SettingsCatalogResponse | null>(null);

  const [selectedGroupId, setSelectedGroupId] = useState<string>(DEFAULT_GROUP_ID);

  const [query, setQuery] = useState('');

  const [error, setError] = useState<string | null>(null);

  const valuesByFullKey = useMemo(() => {
    const out: Record<string, ConfigValue> = {};

    function walk(prefix: string[], node: unknown) {
      if (node === null || typeof node !== 'object' || Array.isArray(node)) {
        out[prefix.join('.')] = node as ConfigValue;
        return;
      }

      for (const [k, v] of Object.entries(node as Record<string, unknown>)) {
        walk([...prefix, k], v);
      }
    }

    walk([], config.values as unknown);

    return out;
  }, [config.values]);

  const [isLoading, setIsLoading] = useState(true);

  const [reloadRevision, setReloadRevision] = useState(0);

  const loadCatalog = useCallback(async (signal: AbortSignal): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetchSettingsCatalog(signal);

      setCatalog(response);

      setSelectedGroupId((current) => {
        const currentExists = response.groups.some((group) => group.id === current);

        if (currentExists) {
          return current;
        }

        return response.groups[0]?.id ?? DEFAULT_GROUP_ID;
      });
    } catch (reason: unknown) {
      if (reason instanceof DOMException && reason.name === 'AbortError') {
        return;
      }

      setError(
        reason instanceof Error
          ? reason.message
          : 'Der Settings-Katalog konnte nicht geladen werden.',
      );
    } finally {
      if (!signal.aborted) {
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    void loadCatalog(controller.signal);

    return () => {
      controller.abort();
    };
  }, [loadCatalog, reloadRevision]);

  const normalizedQuery = normalizeSearchText(query);

  const filteredGroups = useMemo(
    () => filterCatalogGroups(catalog?.groups ?? [], normalizedQuery),
    [catalog, normalizedQuery],
  );

  useEffect(() => {
    if (filteredGroups.length === 0) {
      return;
    }

    const selectedGroupExists = filteredGroups.some(({ group }) => group.id === selectedGroupId);

    if (selectedGroupExists) {
      return;
    }

    const firstGroup = filteredGroups[0];

    if (firstGroup) {
      setSelectedGroupId(firstGroup.group.id);
    }
  }, [filteredGroups, selectedGroupId]);

  const selectedFilteredGroup =
    filteredGroups.find(({ group }) => group.id === selectedGroupId) ?? filteredGroups[0];

  const totalFieldCount = useMemo(() => countCatalogFields(catalog?.groups ?? []), [catalog]);

  const filteredFieldCount = useMemo(
    () =>
      filteredGroups.reduce<number>(
        (total, filteredGroup) => total + countSectionFields(filteredGroup.sections),
        0,
      ),
    [filteredGroups],
  );

  function handleReload(): void {
    setReloadRevision((current) => current + 1);
  }

  if (isLoading && catalog === null) {
    return <SettingsCatalogLoading />;
  }

  if (error !== null && catalog === null) {
    return <SettingsCatalogError message={error} onRetry={handleReload} />;
  }

  if (catalog === null) {
    return null;
  }

  return (
    <div className="flex min-h-full flex-col gap-5">
      {error ? <CatalogWarning message={error} onRetry={handleReload} /> : null}

      <CatalogHeader
        catalog={catalog}
        totalFieldCount={totalFieldCount}
        isLoading={isLoading}
        onReload={handleReload}
        groups={filteredGroups}
        selectedGroupId={selectedFilteredGroup?.group.id}
        query={query}
        onQueryChange={setQuery}
        onSelectGroup={setSelectedGroupId}
        filteredFieldCount={filteredFieldCount}
      />

      <div className="min-h-0 flex-1">
        <main
          className={[
            'min-w-0 overflow-y-auto rounded-2xl border',
            'border-slate-200 bg-slate-50 p-5',
            'dark:border-white/10 dark:bg-slate-950/40',
            'md:p-6',
          ].join(' ')}
        >
          {selectedFilteredGroup ? (
            <GroupPanel
              group={selectedFilteredGroup.group}
              sections={selectedFilteredGroup.sections}
              config={config}
              valuesByFullKey={valuesByFullKey}
            />
          ) : (
            <SettingsCatalogEmpty />
          )}
        </main>
      </div>
    </div>
  );
}

// ============================================================
// Hilfskomponenten
// ============================================================

function CatalogWarning({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div
      className={[
        'flex flex-col gap-3 rounded-xl border border-amber-200',
        'bg-amber-50 p-4 text-amber-900',
        'dark:border-amber-500/20 dark:bg-amber-500/10',
        'dark:text-amber-200 sm:flex-row sm:items-center',
        'sm:justify-between',
      ].join(' ')}
      role="alert"
    >
      <div className="flex min-w-0 items-start gap-3">
        <AlertTriangle size={18} className="mt-0.5 shrink-0" aria-hidden="true" />

        <div className="min-w-0">
          <p className="font-medium">Der Katalog konnte nicht aktualisiert werden.</p>

          <p className="mt-1 text-sm opacity-85">{message}</p>
        </div>
      </div>

      <button type="button" className={secondaryButtonClassName} onClick={onRetry}>
        <RefreshCw size={15} aria-hidden="true" />
        Erneut laden
      </button>
    </div>
  );
}

function CatalogHeader({
  catalog,
  totalFieldCount,
  isLoading,
  onReload,
  groups,
  selectedGroupId,
  query,
  onQueryChange,
  onSelectGroup,
  filteredFieldCount,
}: {
  catalog: SettingsCatalogResponse;
  totalFieldCount: number;
  isLoading: boolean;
  onReload: () => void;
  groups: FilteredGroup[];
  selectedGroupId?: string;
  query: string;
  onQueryChange: (value: string) => void;
  onSelectGroup: (groupId: string) => void;
  filteredFieldCount: number;
}) {
  return (
    <header
      className={[
        'rounded-2xl border border-slate-200 bg-white p-5',
        'shadow-sm dark:border-white/10 dark:bg-slate-900/50',
      ].join(' ')}
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            <span
              className={[
                'inline-flex h-10 w-10 shrink-0 items-center',
                'justify-center rounded-xl bg-blue-50 text-blue-700',
                'dark:bg-blue-500/10 dark:text-blue-300',
              ].join(' ')}
              aria-hidden="true"
            >
              <Settings2 size={20} />
            </span>

            <div>
              <h1 className="text-xl font-semibold text-slate-950 dark:text-white">
                Settings-Katalog
              </h1>

              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                Werte, Ressourcen und Laufzeitmechanismen werden getrennt dargestellt.
              </p>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <CatalogMetaBadge>Schema {catalog.schema_version}</CatalogMetaBadge>

            <CatalogMetaBadge>{catalog.groups.length} Bereiche</CatalogMetaBadge>

            <CatalogMetaBadge>{totalFieldCount} Einträge</CatalogMetaBadge>

            {catalog.request_id ? (
              <CatalogMetaBadge>Anfrage {catalog.request_id}</CatalogMetaBadge>
            ) : null}
          </div>
        </div>
        <div className="mt-4 flex items-center gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-3">
              <label className="text-xs text-slate-500 dark:text-slate-400">Bereich</label>

              <select
                value={selectedGroupId ?? ''}
                onChange={(e) => onSelectGroup(e.target.value)}
                className="rounded border border-slate-300 bg-white px-2 py-1 text-sm text-slate-900 dark:bg-slate-950 dark:text-white"
              >
                {groups.map(({ group }) => (
                  <option key={group.id} value={group.id}>
                    {group.title}
                  </option>
                ))}
              </select>

              <div className="relative flex-1">
                <Search
                  size={16}
                  className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                  aria-hidden="true"
                />

                <input
                  type="search"
                  value={query}
                  placeholder="Katalog durchsuchen …"
                  className="block w-full rounded-lg border border-slate-300 bg-white py-2 pl-9 pr-10 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-white/10 dark:bg-slate-950/60 dark:text-white"
                  onChange={(event) => onQueryChange(event.target.value)}
                />
              </div>
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-2">
            <div className="text-xs text-slate-500 dark:text-slate-400">
              {query
                ? `${groups.length} Bereiche, ${filteredFieldCount} Einträge`
                : `${catalog.groups.length} Bereiche`}
            </div>

            <button
              type="button"
              className={secondaryButtonClassName}
              disabled={isLoading}
              onClick={onReload}
            >
              <RefreshCw
                size={15}
                className={isLoading ? 'animate-spin' : undefined}
                aria-hidden="true"
              />
              Aktualisieren
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

function CatalogSidebar({
  groups,
  selectedGroupId,
  query,
  normalizedQuery,
  filteredFieldCount,
  onQueryChange,
  onSelectGroup,
}: {
  groups: FilteredGroup[];
  selectedGroupId: string | undefined;
  query: string;
  normalizedQuery: string;
  filteredFieldCount: number;
  onQueryChange: (value: string) => void;
  onSelectGroup: (groupId: string) => void;
}) {
  return (
    <aside
      className={[
        'flex min-h-0 flex-col rounded-2xl border',
        'border-slate-200 bg-white shadow-sm',
        'dark:border-white/10 dark:bg-slate-900/50',
      ].join(' ')}
    >
      <div className="border-b border-slate-200 p-4 dark:border-white/10">
        <label htmlFor="settings-catalog-search" className="sr-only">
          Settings-Katalog durchsuchen
        </label>

        <div className="relative">
          <Search
            size={16}
            className={[
              'pointer-events-none absolute left-3 top-1/2',
              '-translate-y-1/2 text-slate-400',
            ].join(' ')}
            aria-hidden="true"
          />

          <input
            id="settings-catalog-search"
            type="search"
            value={query}
            placeholder="Katalog durchsuchen …"
            className={[
              'block w-full rounded-lg border border-slate-300',
              'bg-white py-2 pl-9 pr-10 text-sm text-slate-900',
              'outline-none transition placeholder:text-slate-400',
              'focus:border-blue-500 focus:ring-2',
              'focus:ring-blue-500/20',
              'dark:border-white/10 dark:bg-slate-950/60',
              'dark:text-white',
            ].join(' ')}
            onChange={(event) => {
              onQueryChange(event.target.value);
            }}
          />

          {query ? (
            <button
              type="button"
              className={[
                'absolute right-1.5 top-1/2 inline-flex h-7 w-7',
                '-translate-y-1/2 items-center justify-center',
                'rounded-md text-slate-400 transition',
                'hover:bg-slate-100 hover:text-slate-700',
                'dark:hover:bg-white/10 dark:hover:text-white',
              ].join(' ')}
              aria-label="Suche löschen"
              onClick={() => {
                onQueryChange('');
              }}
            >
              <X size={15} aria-hidden="true" />
            </button>
          ) : null}
        </div>

        {normalizedQuery ? (
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
            {groups.length} Bereiche und {filteredFieldCount} Einträge gefunden
          </p>
        ) : null}
      </div>

      <nav
        className="min-h-0 flex-1 space-y-1 overflow-y-auto p-3"
        aria-label="Settings-Katalogbereiche"
      >
        {groups.length > 0 ? (
          groups.map(({ group, sections }) => {
            const isActive = selectedGroupId === group.id;

            return (
              <button
                key={group.id}
                type="button"
                className={catalogNavigationItemClass(isActive)}
                aria-current={isActive ? 'page' : undefined}
                onClick={() => {
                  onSelectGroup(group.id);
                }}
              >
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-medium">{group.title}</span>

                  <span className="mt-1 block text-xs opacity-70">
                    {countSectionFields(sections)} Einträge
                  </span>
                </span>

                <AvailabilityBadge availability={group.availability} compact />
              </button>
            );
          })
        ) : (
          <div className="rounded-xl border border-dashed border-slate-300 p-5 text-center dark:border-white/10">
            <Search size={20} className="mx-auto text-slate-400" aria-hidden="true" />

            <p className="mt-3 text-sm font-medium text-slate-700 dark:text-slate-300">
              Keine Treffer
            </p>

            <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
              Ändere den Suchbegriff oder lösche die Suche.
            </p>
          </div>
        )}
      </nav>
    </aside>
  );
}

function GroupPanel({ group, sections, config, valuesByFullKey }: GroupPanelProps) {
  const fieldCount = countSectionFields(sections);

  return (
    <section className="space-y-7">
      <header
        className={[
          'rounded-2xl border border-slate-200 bg-white p-5',
          'shadow-sm dark:border-white/10 dark:bg-slate-900/50',
        ].join(' ')}
      >
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-2xl font-semibold text-slate-950 dark:text-white">
                {group.title}
              </h2>

              <AvailabilityBadge availability={group.availability} />
            </div>

            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-400">
              {group.description}
            </p>
          </div>

          <span
            className={[
              'shrink-0 rounded-full bg-slate-100 px-3 py-1.5',
              'text-xs font-medium text-slate-600',
              'dark:bg-white/10 dark:text-slate-300',
            ].join(' ')}
          >
            {fieldCount} Einträge
          </span>
        </div>
      </header>

      {sections.length > 0 ? (
        sections.map((section) => (
          <SectionPanel key={section.id} section={section} config={config} />
        ))
      ) : (
        <SettingsCatalogEmpty />
      )}
    </section>
  );
}

function SectionPanel({ section, config, valuesByFullKey }: SectionPanelProps) {
  return (
    <section className="space-y-3">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            {section.title}
          </h3>

          {section.description ? (
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{section.description}</p>
          ) : null}
        </div>

        <span className="text-xs text-slate-500 dark:text-slate-400">
          {section.fields.length} Einträge
        </span>
      </header>

      <div className="grid gap-3">
        {section.fields.map((field) => (
          <FieldCard
            key={field.id}
            field={field}
            config={config}
            valuesByFullKey={valuesByFullKey}
          />
        ))}
      </div>
    </section>
  );
}

// ============================================================
// FieldCard – vollständig überarbeitet mit Type Guard
// ============================================================

function FieldCard({ field, config, valuesByFullKey }: FieldCardProps) {
  const target = resolveFieldTarget(field);

  const editableConfigField = isEditableConfigField(field);

  const configGroup = editableConfigField ? field.config_group.trim() : null;

  const configKey = editableConfigField ? field.config_key.trim() : null;

  const currentValue =
    configGroup !== null && configKey !== null
      ? getConfigValue(config.values, configGroup, configKey)
      : undefined;

  function handleFieldChange(path: string[], value: ConfigValue): void {
    // If the provider was changed, clear the provider-dependent default model
    if (path.length >= 2 && path[0] === 'models' && path[1] === 'default_provider') {
      const withProvider = updateConfigValue(config.values, path, value);
      const clearedModel = updateConfigValue(withProvider, ['models', 'default_model'], null);
      config.setValues(clearedModel);
      return;
    }

    config.setValues(updateConfigValue(config.values, path, value));
  }

  if (editableConfigField && configGroup !== null && configKey !== null) {
    return (
      <article
        className={[
          'flex min-h-full flex-col rounded-xl border',
          'border-slate-200 bg-white p-4 shadow-sm',
          'dark:border-white/10 dark:bg-slate-900/60',
        ].join(' ')}
      >
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <h4 className="font-semibold text-slate-900 dark:text-slate-100">{field.title}</h4>

            {field.description ? (
              <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-400">
                {field.description}
              </p>
            ) : null}
          </div>

          <AvailabilityBadge availability={field.availability} />
        </div>

        <dl className="mt-4 grid gap-3 text-xs sm:grid-cols-2">
          <MetadataItem
            term="Quelle"
            value={sourceLabel[field.source] ?? formatIdentifier(field.source)}
            icon={<Database size={14} />}
          />

          <MetadataItem
            term="Darstellung"
            value={controlLabel[field.control] ?? formatIdentifier(field.control)}
            icon={<Wrench size={14} />}
          />

          {field.config_group ? (
            <MetadataItem term="Konfigurationsgruppe" value={field.config_group} code />
          ) : null}

          {field.config_key ? (
            <MetadataItem term="Konfigurationsschlüssel" value={field.config_key} code />
          ) : null}

          {target ? (
            <div className="sm:col-span-2">
              <dt className="font-medium text-slate-500 dark:text-slate-400">API-Ziel</dt>

              <dd
                className={[
                  'mt-1 wrap-break-word rounded-md bg-slate-100',
                  'px-2 py-1.5 font-mono text-slate-700',
                  'dark:bg-white/5 dark:text-slate-300',
                ].join(' ')}
              >
                {target}
              </dd>
            </div>
          ) : null}
        </dl>

        {(() => {
          const cfgGroup = field.config_group ?? configGroup;
          const cfgKey = field.config_key ?? configKey;
          const fullKey = `${cfgGroup}.${cfgKey}`;

          function mapControl(c: string): ConfigUIComponent {
            switch (c) {
              case 'textarea':
                return 'textarea';
              case 'number':
                return 'number';
              case 'boolean':
                return 'checkbox';
              case 'multiselect':
                return 'multi_select';
              case 'readonly':
                return 'text';
              case 'select':
              default:
                return 'select';
            }
          }

          const entry: ConfigEntryResponse = {
            group: cfgGroup,
            key: cfgKey,
            full_key: fullKey,
            display_name: field.title,
            description: field.description ?? '',
            value: currentValue === undefined ? null : currentValue,
            default_value: null,
            schema_version: '2.0',
            value_type: undefined,
            value_schema: undefined,
            editable: Boolean(field.editable),
            sensitive: Boolean(field.sensitive),
            secret_configured: false,
            requires_restart: Boolean(field.restart_required ?? false),
            runtime_editable: true,
            nullable: true,
            visibility: '',
            allowed_scopes: [],
            current_scope: '',
            ui: {
              component: mapControl(field.control),
              category: field.config_group ?? undefined,
              section: undefined,
              order: field.order ?? undefined,
              placeholder: null,
              help_text: null,
              unit: null,
              advanced: false,
              hidden: false,
              readonly: !field.editable,
              options: (field.options ?? []).map((o) => ({
                value: o.value,
                label: o.label,
              })),
              dynamic_options: field.endpoint
                ? {
                    source: 'api',
                    endpoint: field.endpoint,
                    value_field: 'value',
                    label_field: 'label',
                    filters: {},
                    depends_on: null,
                    dependency_parameter: null,
                  }
                : null,
            },
          };

          return (
            <SettingsField
              entry={entry}
              path={[cfgGroup, cfgKey]}
              disabled={config.isSaving}
              valuesByFullKey={valuesByFullKey}
              onChange={handleFieldChange}
            />
          );
        })()}

        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          <FieldCapabilityBadge variant="success">editierbar</FieldCapabilityBadge>

          {field.requires_confirmation ? (
            <FieldCapabilityBadge variant="warning">Bestätigung</FieldCapabilityBadge>
          ) : null}

          {field.sensitive ? (
            <FieldCapabilityBadge variant="danger">sensibel</FieldCapabilityBadge>
          ) : null}

          {field.restart_required ? (
            <FieldCapabilityBadge variant="warning">Neustart erforderlich</FieldCapabilityBadge>
          ) : null}
        </div>
      </article>
    );
  }

  return (
    <article
      className={[
        'flex min-h-full flex-col rounded-xl border border-slate-200',
        'bg-white p-4 shadow-sm transition',
        'hover:border-slate-300 hover:shadow-md',
        'dark:border-white/10 dark:bg-slate-900/60',
        'dark:hover:border-white/20',
      ].join(' ')}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h4 className="font-semibold text-slate-900 dark:text-slate-100">{field.title}</h4>

          {field.description ? (
            <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-400">
              {field.description}
            </p>
          ) : null}
        </div>

        <AvailabilityBadge availability={field.availability} />
      </div>

      <dl className="mt-4 grid gap-3 text-xs sm:grid-cols-2">
        <MetadataItem
          term="Quelle"
          value={sourceLabel[field.source] ?? formatIdentifier(field.source)}
          icon={<Database size={14} />}
        />

        <MetadataItem
          term="Darstellung"
          value={controlLabel[field.control] ?? formatIdentifier(field.control)}
          icon={<Wrench size={14} />}
        />

        {field.config_group ? (
          <MetadataItem term="Konfigurationsgruppe" value={field.config_group} code />
        ) : null}

        {field.config_key ? (
          <MetadataItem term="Konfigurationsschlüssel" value={field.config_key} code />
        ) : null}

        {target ? (
          <div className="sm:col-span-2">
            <dt className="font-medium text-slate-500 dark:text-slate-400">API-Ziel</dt>

            <dd
              className={[
                'mt-1 wrap-break-word rounded-md bg-slate-100',
                'px-2 py-1.5 font-mono text-slate-700',
                'dark:bg-white/5 dark:text-slate-300',
              ].join(' ')}
            >
              {target}
            </dd>
          </div>
        ) : null}
      </dl>

      {field.source === 'resource' && target && field.availability === 'available' ? (
        <a
          href={target}
          className={[
            'mt-4 inline-flex items-center justify-center gap-2',
            'rounded-lg border border-slate-300 bg-white px-3 py-2',
            'text-sm font-medium text-slate-700 transition',
            'hover:bg-slate-50',
            'dark:border-white/10 dark:bg-white/5 dark:text-slate-200',
            'dark:hover:bg-white/10',
          ].join(' ')}
        >
          <ExternalLink size={15} aria-hidden="true" />
          Ressource öffnen
        </a>
      ) : null}

      <div className="mt-auto flex flex-wrap gap-2 pt-4 text-xs">
        {field.editable ? (
          currentValue === undefined && field.source === 'config' ? (
            <FieldCapabilityBadge variant="warning">Config-Wert fehlt</FieldCapabilityBadge>
          ) : (
            <FieldCapabilityBadge variant="success">editierbar</FieldCapabilityBadge>
          )
        ) : (
          <FieldCapabilityBadge variant="neutral">schreibgeschützt</FieldCapabilityBadge>
        )}

        {field.requires_confirmation ? (
          <FieldCapabilityBadge variant="warning">Bestätigung</FieldCapabilityBadge>
        ) : null}

        {field.sensitive ? (
          <FieldCapabilityBadge variant="danger">sensibel</FieldCapabilityBadge>
        ) : null}

        {field.restart_required ? (
          <FieldCapabilityBadge variant="warning">Neustart erforderlich</FieldCapabilityBadge>
        ) : null}
      </div>
    </article>
  );
}

// ============================================================
// Weitere Hilfskomponenten
// ============================================================

function MetadataItem({
  term,
  value,
  icon,
  code = false,
}: {
  term: string;
  value: string;
  icon?: ReactNode;
  code?: boolean;
}) {
  return (
    <div>
      <dt className="flex items-center gap-1.5 font-medium text-slate-500 dark:text-slate-400">
        {icon ? <span aria-hidden="true">{icon}</span> : null}

        {term}
      </dt>

      <dd
        className={[
          'mt-1 wrap-break-word text-slate-700 dark:text-slate-300',
          code ? 'font-mono' : '',
        ].join(' ')}
      >
        {value}
      </dd>
    </div>
  );
}

function AvailabilityBadge({
  availability,
  compact = false,
}: {
  availability: SettingsAvailability;
  compact?: boolean;
}) {
  const icon =
    availability === 'available' ? (
      <CheckCircle2 size={13} aria-hidden="true" />
    ) : availability === 'prepared' ? (
      <Wrench size={13} aria-hidden="true" />
    ) : (
      <Clock3 size={13} aria-hidden="true" />
    );

  return (
    <span
      className={[
        'inline-flex shrink-0 items-center gap-1 rounded-full',
        'border px-2 py-1 text-xs font-medium',
        availabilityBadgeClass(availability),
        compact ? 'max-w-27.5' : '',
      ].join(' ')}
      title={badgeLabel[availability]}
    >
      {icon}

      {!compact ? <span>{badgeLabel[availability]}</span> : null}
    </span>
  );
}

function FieldCapabilityBadge({
  variant,
  children,
}: {
  variant: 'neutral' | 'success' | 'warning' | 'danger';
  children: string;
}) {
  const className =
    variant === 'success'
      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300'
      : variant === 'warning'
        ? 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300'
        : variant === 'danger'
          ? 'bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-300'
          : 'bg-slate-100 text-slate-600 dark:bg-white/10 dark:text-slate-300';

  return (
    <span className={['rounded-md px-2 py-1 font-medium', className].join(' ')}>{children}</span>
  );
}

function CatalogMetaBadge({ children }: { children: ReactNode }) {
  return (
    <span className="rounded-full bg-slate-100 px-2.5 py-1 font-medium text-slate-600 dark:bg-white/10 dark:text-slate-300">
      {children}
    </span>
  );
}

function SettingsCatalogLoading() {
  return (
    <div
      className={[
        'flex min-h-105 items-center justify-center rounded-2xl',
        'border border-slate-200 bg-white p-8',
        'dark:border-white/10 dark:bg-slate-900/50',
      ].join(' ')}
      aria-live="polite"
      aria-busy="true"
    >
      <div className="text-center">
        <span
          className={[
            'mx-auto block h-8 w-8 animate-spin rounded-full',
            'border-2 border-slate-300 border-t-blue-600',
          ].join(' ')}
          aria-hidden="true"
        />

        <p className="mt-4 font-medium text-slate-700 dark:text-slate-300">
          Settings-Katalog wird geladen …
        </p>

        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Bereiche und vorbereitete Ressourcen werden vom Backend abgerufen.
        </p>
      </div>
    </div>
  );
}

function SettingsCatalogError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div
      className={[
        'rounded-2xl border border-red-200 bg-red-50 p-6',
        'text-red-900 dark:border-red-500/20',
        'dark:bg-red-500/10 dark:text-red-200',
      ].join(' ')}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <ShieldAlert size={22} className="mt-0.5 shrink-0" aria-hidden="true" />

        <div className="min-w-0">
          <h2 className="font-semibold">Settings-Katalog nicht verfügbar</h2>

          <p className="mt-2 text-sm leading-6">{message}</p>

          <button
            type="button"
            className={[secondaryButtonClassName, 'mt-4'].join(' ')}
            onClick={onRetry}
          >
            <RefreshCw size={15} aria-hidden="true" />
            Erneut laden
          </button>
        </div>
      </div>
    </div>
  );
}

function SettingsCatalogEmpty() {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center dark:border-white/10 dark:bg-slate-900/40">
      <Settings2 size={24} className="mx-auto text-slate-400" aria-hidden="true" />

      <h2 className="mt-3 font-semibold text-slate-900 dark:text-white">
        Keine Einstellungen gefunden
      </h2>

      <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
        Der ausgewählte Bereich enthält derzeit keine sichtbaren Einträge.
      </p>
    </div>
  );
}

// ============================================================
// Hilfsfunktionen
// ============================================================

function getConfigValue(values: ConfigObject, group: string, key: string): ConfigValue | undefined {
  const groupValue = values[group];

  if (!isConfigObject(groupValue)) {
    return undefined;
  }

  return groupValue[key];
}

function updateConfigValue(source: ConfigObject, path: string[], value: ConfigValue): ConfigObject {
  const [currentKey, ...remainingPath] = path;

  if (currentKey === undefined) {
    return source;
  }

  if (remainingPath.length === 0) {
    return {
      ...source,
      [currentKey]: value,
    };
  }

  const currentValue = source[currentKey];

  const nestedSource: ConfigObject = isConfigObject(currentValue) ? currentValue : {};

  return {
    ...source,
    [currentKey]: updateConfigValue(nestedSource, remainingPath, value),
  };
}

function isConfigObject(value: ConfigValue | undefined): value is ConfigObject {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function filterCatalogGroups(groups: SettingsGroupDescriptor[], query: string): FilteredGroup[] {
  return groups
    .slice()
    .sort((left, right) => left.order - right.order)
    .flatMap((group) => {
      const groupMatches = matchesText(query, group.id, group.title, group.description);

      const sections = group.sections
        .slice()
        .sort((left, right) => left.order - right.order)
        .flatMap((section) => {
          const sectionMatches = matchesText(query, section.id, section.title, section.description);

          const orderedFields = section.fields
            .slice()
            .sort((left, right) => left.order - right.order);

          const fields = orderedFields.filter(
            (field) => groupMatches || sectionMatches || matchesField(field, query),
          );

          if (query && !groupMatches && !sectionMatches && fields.length === 0) {
            return [];
          }

          return [
            {
              ...section,
              fields: groupMatches || sectionMatches ? orderedFields : fields,
            },
          ];
        });

      if (query && !groupMatches && sections.length === 0) {
        return [];
      }

      return [
        {
          group,
          sections: groupMatches
            ? group.sections
                .slice()
                .sort((left, right) => left.order - right.order)
                .map((section) => ({
                  ...section,
                  fields: section.fields.slice().sort((left, right) => left.order - right.order),
                }))
            : sections,
        },
      ];
    });
}

function matchesField(field: SettingsFieldDescriptor, query: string): boolean {
  return matchesText(
    query,
    field.id,
    field.title,
    field.description,
    field.source,
    field.control,
    field.endpoint,
    field.config_group,
    field.config_key,
    ...field.tags,
  );
}

function matchesText(query: string, ...values: Array<string | null | undefined>): boolean {
  if (!query) {
    return true;
  }

  return values.some(
    (value) => value !== undefined && value !== null && normalizeSearchText(value).includes(query),
  );
}

function normalizeSearchText(value: string): string {
  return value.replace(/[_-]+/g, ' ').toLocaleLowerCase('de').trim();
}

function countCatalogFields(groups: SettingsGroupDescriptor[]): number {
  return groups.reduce<number>((total, group) => total + countSectionFields(group.sections), 0);
}

function countSectionFields(sections: SettingsSectionDescriptor[]): number {
  return sections.reduce<number>((total, section) => total + section.fields.length, 0);
}

// ============================================================
// resolveFieldTarget – typstabilere Version
// ============================================================

function resolveFieldTarget(field: SettingsFieldDescriptor): string | undefined {
  if (typeof field.endpoint === 'string' && field.endpoint.trim().length > 0) {
    return field.endpoint;
  }

  if (
    typeof field.config_group === 'string' &&
    field.config_group.trim().length > 0 &&
    typeof field.config_key === 'string' &&
    field.config_key.trim().length > 0
  ) {
    return [
      '/api/v1/config',
      encodeURIComponent(field.config_group.trim()),
      encodeURIComponent(field.config_key.trim()),
    ].join('/');
  }

  return undefined;
}

// ============================================================
// Formatierungen und Styling
// ============================================================

function formatIdentifier(value: string): string {
  return value.replace(/[_-]+/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase());
}

function availabilityBadgeClass(availability: SettingsAvailability): string {
  switch (availability) {
    case 'available':
      return [
        'border-emerald-200 bg-emerald-50 text-emerald-700',
        'dark:border-emerald-500/20 dark:bg-emerald-500/10',
        'dark:text-emerald-300',
      ].join(' ');

    case 'prepared':
      return [
        'border-amber-200 bg-amber-50 text-amber-700',
        'dark:border-amber-500/20 dark:bg-amber-500/10',
        'dark:text-amber-300',
      ].join(' ');

    case 'planned':
      return [
        'border-slate-200 bg-slate-100 text-slate-600',
        'dark:border-white/10 dark:bg-white/5 dark:text-slate-300',
      ].join(' ');
  }
}

function catalogNavigationItemClass(isActive: boolean): string {
  return [
    'flex w-full items-center gap-3 rounded-xl px-3 py-3',
    'text-left text-sm transition',
    'focus-visible:outline-none focus-visible:ring-2',
    'focus-visible:ring-blue-500 focus-visible:ring-offset-2',
    'dark:focus-visible:ring-offset-slate-900',
    isActive
      ? ['bg-slate-900 text-white shadow-sm', 'dark:bg-slate-100 dark:text-slate-950'].join(' ')
      : ['text-slate-700 hover:bg-slate-100', 'dark:text-slate-300 dark:hover:bg-white/5'].join(
          ' ',
        ),
  ].join(' ');
}

const secondaryButtonClassName = [
  'inline-flex items-center justify-center gap-2 rounded-lg',
  'border border-slate-300 bg-white px-3.5 py-2',
  'text-sm font-medium text-slate-700 transition',
  'hover:bg-slate-50',
  'focus-visible:outline-none focus-visible:ring-2',
  'focus-visible:ring-blue-500 focus-visible:ring-offset-2',
  'disabled:cursor-not-allowed disabled:opacity-50',
  'dark:border-white/10 dark:bg-white/5 dark:text-slate-200',
  'dark:hover:bg-white/10 dark:focus-visible:ring-offset-slate-950',
].join(' ');
