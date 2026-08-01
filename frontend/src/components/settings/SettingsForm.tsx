// Extracted SettingsForm, SettingsSingleSection and SettingsSection
import React from 'react';
import type { ConfigValue, ConfigEntryResponse, ConfigObject } from '../../contracts/config';

interface SettingsFieldOption {
  value: string | number | boolean;
  label: string;
  description?: string;
}

interface InferredFieldMetadata {
  description?: string;
  sensitive?: boolean;
  readOnly?: boolean;
  required?: boolean;
  placeholder?: string | null;
  minimum?: number;
  maximum?: number;
  step?: number;
  options?: SettingsFieldOption[];
}
import { SettingsField } from './SettingsField';

function formatSettingLabel(value: string): string {
  return value.replace(/[_-]+/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase());
}

function normalizeText(value: string): string {
  return value.replace(/[_-]+/g, ' ').toLocaleLowerCase('de');
}

function countConfigValues(value: ConfigValue | ConfigObject | undefined): number {
  if (value === undefined) {
    return 0;
  }

  if (
    value === null ||
    typeof value === 'string' ||
    typeof value === 'number' ||
    typeof value === 'boolean'
  ) {
    return 1;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return 1;
    }

    return value.reduce<number>((count, item) => count + countConfigValues(item), 0);
  }

  const childValues: ConfigValue[] = Object.values(value);

  if (childValues.length === 0) {
    return 1;
  }

  return childValues.reduce<number>(
    (count, childValue) => count + countConfigValues(childValue),
    0,
  );
}

function isConfigObject(value: unknown): value is ConfigObject {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return false;
  }

  return Object.values(value).every(isConfigValue);
}

function isConfigValue(value: unknown): value is ConfigValue {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') {
    return true;
  }

  if (typeof value === 'number') {
    return Number.isFinite(value);
  }

  if (Array.isArray(value)) {
    return value.every(isConfigValue);
  }

  return isConfigObject(value);
}

function isConfigRecord(value: ConfigValue | undefined): value is ConfigObject {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function includesAny(value: string, candidates: string[]): boolean {
  return candidates.some((candidate) => value.includes(candidate));
}

function inferFieldMetadata({ fieldKey, path, value }: { fieldKey: string; path: string[]; value: ConfigValue; }) {
  const normalizedKey = fieldKey.toLocaleLowerCase('de');

  const normalizedPath = path.join('.').toLocaleLowerCase('de');

  const metadata: InferredFieldMetadata = {};

  if (
    includesAny(normalizedKey, [
      'secret',
      'password',
      'passwort',
      'token',
      'api_key',
      'apikey',
      'credential',
    ])
  ) {
    metadata.sensitive = true;

    metadata.description =
      'Sensible Werte sollten als Secret-Referenz und nicht als Klartext gespeichert werden.';
  }

  if (
    includesAny(normalizedKey, [
      'description',
      'beschreibung',
      'prompt',
      'instruction',
      'anweisung',
    ])
  ) {
    metadata.description ??= 'Mehrzeiliger Textwert für die dynamische Laufzeitkonfiguration.';
  }

  if (normalizedKey === 'timezone' || normalizedKey === 'time_zone') {
    metadata.placeholder = 'Europe/Berlin';

    metadata.required = true;
  }

  if (normalizedKey === 'language' || normalizedKey === 'locale') {
    metadata.options = [
      {
        value: 'de',
        label: 'Deutsch',
      },
      {
        value: 'en',
        label: 'Englisch',
      },
    ];
  }

  if (normalizedKey === 'theme') {
    metadata.options = [
      {
        value: 'system',
        label: 'System',
      },
      {
        value: 'light',
        label: 'Hell',
      },
      {
        value: 'dark',
        label: 'Dunkel',
      },
    ];
  }

  if (normalizedKey === 'environment') {
    metadata.options = [
      {
        value: 'development',
        label: 'Development',
      },
      {
        value: 'intranet',
        label: 'Intranet',
      },
      {
        value: 'internet',
        label: 'Internet',
      },
    ];
  }

  if (normalizedKey === 'autonomy_level' || normalizedKey === 'autonomy') {
    metadata.options = [
      {
        value: 'advisory',
        label: 'Nur beraten',
      },
      {
        value: 'draft',
        label: 'Entwürfe erstellen',
      },
      {
        value: 'prepare',
        label: 'Änderungen vorbereiten',
      },
      {
        value: 'execute_approved',
        label: 'Freigegebene Aktionen ausführen',
      },
    ];
  }

  if (includesAny(normalizedKey, ['temperature', 'top_p', 'min_p'])) {
    metadata.minimum = 0;

    metadata.maximum = normalizedKey === 'temperature' ? 2 : 1;

    metadata.step = 0.01;
  }

  if (includesAny(normalizedKey, ['timeout', 'duration']) && typeof value === 'number') {
    metadata.minimum = 0;

    metadata.step = 1;
  }

  if (
    includesAny(normalizedKey, ['max_', 'limit', 'count', 'retries', 'rounds', 'steps']) &&
    typeof value === 'number'
  ) {
    metadata.minimum ??= 0;

    metadata.step ??= 1;
  }

  if (
    includesAny(normalizedPath, [
      'revision',
      'status',
      'health',
      'latency',
      'error_rate',
      'registry_revision',
    ])
  ) {
    metadata.readOnly = true;

    metadata.description ??=
      'Dieser Wert wird vom Backend ermittelt und ist in dieser Ansicht schreibgeschützt.';
  }

  if (includesAny(normalizedKey, ['endpoint', 'base_url', 'url', 'webhook'])) {
    metadata.placeholder = 'https://example.org';
  }

  return metadata;
}

function matchesSearchQuery(key: string, value: ConfigValue | undefined, searchQuery: string): boolean {
  if (!searchQuery) {
    return true;
  }

  if (normalizeText(key).includes(searchQuery)) {
    return true;
  }

  if (value === undefined) {
    return false;
  }

  if (typeof value === 'string') {
    return normalizeText(value).includes(searchQuery);
  }

  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value).toLocaleLowerCase('de').includes(searchQuery);
  }

  if (value === null) {
    return false;
  }

  if (Array.isArray(value)) {
    return value.some((item, index) => matchesSearchQuery(String(index), item, searchQuery));
  }

  return Object.entries(value).some(([childKey, childValue]) =>
    matchesSearchQuery(childKey, childValue, searchQuery),
  );
}

function SettingsEmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center dark:border-white/15 dark:bg-slate-900/40">
      <h3 className="font-semibold text-slate-900 dark:text-white">{title}</h3>

      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500 dark:text-slate-400">
        {description}
      </p>
    </div>
  );
}

export function SettingsForm({
  entries,
  disabled,
  searchQuery,
  totalEntryCount,
  onChange,
  valuesByFullKey,
  entriesByFullKey,
}: {
  entries: [string, ConfigValue][];
  disabled: boolean;
  searchQuery: string;
  totalEntryCount: number;
  onChange: (path: string[], value: ConfigValue) => void;
  valuesByFullKey?: Record<string, ConfigValue> | null;
  entriesByFullKey?: Record<string, ConfigEntryResponse> | null;
}) {
  if (totalEntryCount === 0) {
    return (
      <SettingsEmptyState
        title="Keine Einstellungen vorhanden"
        description="Der Server hat derzeit keine fachliche Konfiguration ausgeliefert."
      />
    );
  }

  if (entries.length === 0) {
    return (
      <SettingsEmptyState
        title="Keine passenden Einstellungen"
        description="Für den eingegebenen Suchbegriff wurden keine Konfigurationswerte gefunden."
      />
    );
  }

  return (
    <div className="space-y-5">
      {entries.map(([sectionKey, sectionValue]) => (
        <SettingsSection
          key={sectionKey}
          sectionKey={sectionKey}
          value={sectionValue}
          disabled={disabled}
          searchQuery={searchQuery}
          onChange={onChange}
          valuesByFullKey={valuesByFullKey}
          entriesByFullKey={entriesByFullKey ?? null}
        />
      ))}
    </div>
  );
}

export function SettingsSingleSection({
  sectionKey,
  value,
  disabled,
  searchQuery,
  onChange,
  valuesByFullKey,
  entriesByFullKey,
}: {
  sectionKey: string;
  value: ConfigValue | undefined;
  disabled: boolean;
  searchQuery: string;
  onChange: (path: string[], value: ConfigValue) => void;
  valuesByFullKey?: Record<string, ConfigValue> | null;
  entriesByFullKey?: Record<string, ConfigEntryResponse> | null;
}) {
  if (value === undefined || value === null) {
    return (
      <SettingsEmptyState
        title="Keine Einstellungen vorhanden"
        description="Diese Kategorie enthält derzeit keine Konfigurationswerte."
      />
    );
  }

  if (searchQuery && !matchesSearchQuery(sectionKey, value, searchQuery)) {
    return (
      <SettingsEmptyState
        title="Keine passenden Einstellungen"
        description="In dieser Kategorie wurden keine passenden Werte gefunden."
      />
    );
  }

  return (
    <SettingsSection
      sectionKey={sectionKey}
      value={value}
      disabled={disabled}
      searchQuery={searchQuery}
      onChange={onChange}
      valuesByFullKey={valuesByFullKey}
      entriesByFullKey={entriesByFullKey}
    />
  );
}

function SettingsSection({
  sectionKey,
  value,
  disabled,
  searchQuery,
  path = [],
  depth = 0,
  onChange,
  valuesByFullKey,
  entriesByFullKey,
}: {
  sectionKey: string;
  value: ConfigValue;
  disabled: boolean;
  searchQuery: string;
  path?: string[];
  depth?: number;
  onChange: (path: string[], value: ConfigValue) => void;
  valuesByFullKey?: Record<string, ConfigValue> | null;
  entriesByFullKey?: Record<string, ConfigEntryResponse> | null;
}) {
  const currentPath = [...path, sectionKey];

  const label = formatSettingLabel(sectionKey);
  const sectionFullKey = currentPath.join('.');

  const MAX_RENDER_DEPTH = 12;

  if (depth > MAX_RENDER_DEPTH) {
    const inferredEntryMaxDepth: ConfigEntryResponse = {
      group: sectionKey,
      key: sectionKey,
      full_key: sectionFullKey,
      display_name: label,
      description:
        'Die maximale Darstellungstiefe wurde erreicht. Der Wert kann als JSON bearbeitet werden.',
      value: value,
      default_value: null,
      schema_version: '2.0',
      value_type: undefined,
      value_schema: undefined,
      editable: true,
      sensitive: false,
      secret_configured: false,
      requires_restart: false,
      runtime_editable: true,
      nullable: true,
      visibility: '',
      allowed_scopes: [],
      current_scope: '',
      ui: {
        component: undefined,
        category: undefined,
        section: undefined,
        order: undefined,
        placeholder: null,
        help_text: null,
        unit: null,
        advanced: false,
        hidden: false,
        readonly: false,
        options: [],
        dynamic_options: null,
      },
      permissions: {
        read: 'config:read',
        write: 'config:write',
        reveal_secret: null,
      },
    };

    return (
      <SettingsField
        entry={inferredEntryMaxDepth}
        path={currentPath}
        disabled={disabled}
        valuesByFullKey={valuesByFullKey}
        onChange={onChange}
      />
    );
  }

  if (!isConfigRecord(value)) {
    if (searchQuery && !matchesSearchQuery(sectionKey, value, searchQuery)) {
      return null;
    }

    const existingEntry = entriesByFullKey ? entriesByFullKey[sectionFullKey] : undefined;

    if (existingEntry) {
      return (
        <SettingsField
          entry={existingEntry}
          path={currentPath}
          disabled={disabled}
          valuesByFullKey={valuesByFullKey}
          onChange={onChange}
        />
      );
    }

    const metadata = inferFieldMetadata({
      fieldKey: sectionKey,
      path: currentPath,
      value,
    });
    const inferredEntryLeaf: ConfigEntryResponse = {
      group: sectionKey,
      key: sectionKey,
      full_key: sectionFullKey,
      display_name: label,
      description: metadata.description ?? '',
      value: value,
      default_value: null,
      schema_version: '2.0',
      value_type: undefined,
      value_schema: undefined,
      editable: metadata.readOnly ? false : true,
      sensitive: Boolean(metadata.sensitive),
      secret_configured: false,
      requires_restart: false,
      runtime_editable: true,
      nullable: !(metadata.required ?? false),
      visibility: '',
      allowed_scopes: [],
      current_scope: '',
      ui: {
        component: undefined,
        category: undefined,
        section: undefined,
        order: undefined,
        placeholder: metadata.placeholder ?? null,
        help_text: null,
        unit: null,
        advanced: false,
        hidden: false,
        readonly: Boolean(metadata.readOnly),
        options: (metadata.options ?? []).map((o: SettingsFieldOption) => ({
          value: o.value,
          label: o.label,
          description: o.description,
        })),
        dynamic_options: null,
      },
      permissions: {
        read: 'config:read',
        write: 'config:write',
        reveal_secret: null,
      },
    };

    return (
      <SettingsField
        entry={inferredEntryLeaf}
        path={currentPath}
        disabled={disabled}
        valuesByFullKey={valuesByFullKey}
        onChange={onChange}
      />
    );
  }

  const visibleEntries = Object.entries(value)
    .filter(([childKey, childValue]) => matchesSearchQuery(childKey, childValue, searchQuery))
    .sort((left, right) =>
      formatSettingLabel(left[0]).localeCompare(formatSettingLabel(right[0]), 'de', {
        sensitivity: 'base',
      }),
    );

  if (
    searchQuery &&
    visibleEntries.length === 0 &&
    !normalizeText(sectionKey).includes(searchQuery)
  ) {
    return null;
  }

  return (
    <section
      className={[
        'overflow-hidden rounded-2xl border border-slate-200',
        'bg-slate-100/60',
        'dark:border-white/10 dark:bg-white/3',
      ].join(' ')}
    >
      <header
        className={[
          'border-b border-slate-200 bg-white px-5 py-4',
          'dark:border-white/10 dark:bg-slate-900/60',
        ].join(' ')}
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-semibold text-slate-950 dark:text-white">{label}</h2>

            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {getSectionDescription(sectionKey)}
            </p>
          </div>

          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 dark:bg-white/10 dark:text-slate-300">
            {countConfigValues(value)} Werte
          </span>
        </div>

        <code className="mt-3 inline-block rounded bg-slate-100 px-2 py-1 text-xs text-slate-500 dark:bg-white/5 dark:text-slate-400">
          {currentPath.join('.')}
        </code>
      </header>

      <div className="grid gap-4 p-4 grid-cols-1">
        {visibleEntries.map(([fieldKey, fieldValue]) => (
          <SettingsSection
            key={fieldKey}
            sectionKey={fieldKey}
            value={fieldValue}
            disabled={disabled}
            searchQuery={searchQuery}
            path={currentPath}
            depth={depth + 1}
            onChange={onChange}
            valuesByFullKey={valuesByFullKey}
            entriesByFullKey={entriesByFullKey ?? null}
          />
        ))}
      </div>
    </section>
  );
}

function getSectionDescription(key: string): string {
  const normalizedKey = key.toLocaleLowerCase('de');

  const descriptions: Record<string, string> = {
    identity: 'Identität, Grundauftrag und allgemeines Verhalten von Kernschmied.',
    behavior: 'Kommunikationsverhalten, Autonomie und Selbstprüfung.',
    prompts: 'Versionierte System- und Aufgabenprompts sowie deren Vererbung.',
    models: 'Modelle, Auswahlregeln und Generierungsparameter.',
    providers: 'Verbindungen, Timeouts und Laufzeitwerte der Modellprovider.',
    tools: 'Tool-Auswahl, Ausführungsgrenzen und Bestätigungspflichten.',
    knowledge: 'Wissensquellen, Gedächtnis und Kontextauswahl.',
    context: 'Kontextgrenzen, Quellenprioritäten und Relevanzregeln.',
    workflow: 'Planung, Ausführung, Selbstprüfung und Abschluss von Aufgaben.',
    runtime: 'Globale Laufzeitgrenzen und operative Systemwerte.',
    storage: 'Speicherziele, Versionierung und Aufbewahrung.',
    communication: 'Kommunikationskanäle und Interaktionsverhalten.',
    appearance: 'Darstellung, Theme und lokale Oberflächenpräferenzen.',
    security: 'Sicherheitsgrenzen, Autorisierung und Bestätigungspflichten.',
    diagnostics: 'Diagnose-, Qualitäts- und Laufzeitinformationen.',
    learning: 'Lernkandidaten, Bewertung und kontrollierte Optimierung.',
  };

  return descriptions[normalizedKey] ?? `Konfigurationsbereich „${formatSettingLabel(key)}“.`;
}

export default SettingsForm;
