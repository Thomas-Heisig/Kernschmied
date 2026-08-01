// F:\Kernschmied\frontend\src\components\settings\SettingsContent.tsx

import { useEffect, useMemo, useState } from "react";

import type { ReactNode } from "react";

import {
  Check,
  Clipboard,
  RefreshCw,
  RotateCcw,
  Save,
  Search,
  X,
} from "lucide-react";

import type { ConfigObject, ConfigValue } from "../../contracts/config";
import type { UseSystemConfigReturn } from "../../hooks/useSystemConfig";
import { SettingsCatalogView } from "./SettingsCatalogView";
import { SettingsField } from "./SettingsField";

interface SettingsContentProps {
  activeKey: string | null;
  showJson: boolean;
  config: UseSystemConfigReturn;
}

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
  placeholder?: string;
  minimum?: number;
  maximum?: number;
  step?: number;
  options?: SettingsFieldOption[];
}

interface SettingsSectionProps {
  sectionKey: string;
  value: ConfigValue;
  disabled: boolean;
  searchQuery: string;
  path?: string[];
  depth?: number;
  onChange: (path: string[], value: ConfigValue) => void;
}

const SETTINGS_CATALOG_KEY = "settings-catalog";

const MAX_RENDER_DEPTH = 12;

export function SettingsContent({
  activeKey,
  showJson,
  config,
}: SettingsContentProps) {
  const {
    values,
    revision,
    isLoading,
    isSaving,
    isDirty,
    error,
    setValues,
    reload,
    save,
    reset,
  } = config;

  const [jsonDraft, setJsonDraft] = useState("");

  const [jsonError, setJsonError] = useState<string | null>(null);

  const [isJsonDraftDirty, setIsJsonDraftDirty] = useState(false);

  const [jsonCopied, setJsonCopied] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");

  const normalizedSearchQuery = searchQuery.trim().toLocaleLowerCase("de");

  const sectionEntries = useMemo(
    () =>
      Object.entries(values).sort((left, right) =>
        formatSettingLabel(left[0]).localeCompare(
          formatSettingLabel(right[0]),
          "de",
          {
            sensitivity: "base",
          },
        ),
      ),
    [values],
  );

  const visibleSectionEntries = useMemo(
    () =>
      sectionEntries.filter(([sectionKey, sectionValue]) =>
        matchesSearchQuery(sectionKey, sectionValue, normalizedSearchQuery),
      ),
    [sectionEntries, normalizedSearchQuery],
  );

  const totalSettingCount = useMemo(() => countConfigValues(values), [values]);

  const visibleSettingCount = useMemo(
    () =>
      visibleSectionEntries.reduce(
        (count, [, sectionValue]) => count + countConfigValues(sectionValue),
        0,
      ),
    [visibleSectionEntries],
  );

  const entriesByFullKey = (config as any).entriesByFullKey as
    | Record<string, any>
    | null
    | undefined;

  const valuesByFullKey = useMemo(() => {
    // Prefer the richer `entriesByFullKey` if provided by the hook.
    if (entriesByFullKey && typeof entriesByFullKey === "object") {
      const out: Record<string, ConfigValue> = {};

      for (const [full, entry] of Object.entries(entriesByFullKey)) {
        out[full] = (entry as any).value;
      }

      return out;
    }

    const out: Record<string, ConfigValue> = {};

    function walk(prefix: string[], node: any) {
      if (node === null || typeof node !== "object") {
        out[prefix.join(".")] = node as ConfigValue;
        return;
      }

      for (const [k, v] of Object.entries(node)) {
        walk([...prefix, k], v);
      }
    }

    walk([], values as any);

    return out;
  }, [values, entriesByFullKey]);

  useEffect(() => {
    if (!showJson) {
      setIsJsonDraftDirty(false);
      setJsonError(null);
      return;
    }

    if (isJsonDraftDirty) {
      return;
    }

    setJsonDraft(JSON.stringify(values, null, 2));

    setJsonError(null);
  }, [showJson, values, isJsonDraftDirty]);

  useEffect(() => {
    setSearchQuery("");
  }, [activeKey, showJson]);

  useEffect(() => {
    if (!jsonCopied) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setJsonCopied(false);
    }, 1_500);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [jsonCopied]);

  if (isLoading) {
    return <SettingsLoadingState />;
  }

  if (!showJson && activeKey === SETTINGS_CATALOG_KEY) {
    return (
      <div className="min-h-full overflow-y-auto bg-slate-50 p-5 dark:bg-slate-950/30 md:p-8">
        <SettingsCatalogView config={config} />
      </div>
    );
  }

  function handleApplyJson(): void {
    const parsedResult = parseConfigObject(jsonDraft);

    if (!parsedResult.ok) {
      setJsonError(parsedResult.error);
      return;
    }

    setValues(parsedResult.value);

    setJsonDraft(JSON.stringify(parsedResult.value, null, 2));

    setJsonError(null);
    setIsJsonDraftDirty(false);
  }

  function handleFormatJson(): void {
    const parsedResult = parseConfigObject(jsonDraft);

    if (!parsedResult.ok) {
      setJsonError(parsedResult.error);
      return;
    }

    setJsonDraft(JSON.stringify(parsedResult.value, null, 2));

    setJsonError(null);
  }

  function handleResetJsonDraft(): void {
    setJsonDraft(JSON.stringify(values, null, 2));

    setJsonError(null);
    setIsJsonDraftDirty(false);
  }

  async function handleCopyJson(): Promise<void> {
    try {
      await navigator.clipboard.writeText(jsonDraft);

      setJsonCopied(true);
    } catch {
      setJsonError(
        "Die JSON-Konfiguration konnte nicht in die Zwischenablage kopiert werden.",
      );
    }
  }

  function handleJsonDraftChange(nextValue: string): void {
    setJsonDraft(nextValue);
    setIsJsonDraftDirty(true);

    if (jsonError !== null) {
      setJsonError(null);
    }
  }

  function handleFieldChange(path: string[], value: ConfigValue): void {
    // If the default provider is changed, also clear the dependent default_model
    if (
      path.length >= 2 &&
      path[0] === "models" &&
      path[1] === "default_provider"
    ) {
      const withProvider = updateConfigValue(values, path, value);
      const clearedModel = updateConfigValue(
        withProvider,
        ["models", "default_model"],
        null,
      );
      setValues(clearedModel);
      return;
    }

    setValues(updateConfigValue(values, path, value));
  }

  function handleReload(): void {
    void reload();
  }

  function handleSave(): void {
    void save();
  }

  function handleReset(): void {
    reset();
    setJsonError(null);
    setIsJsonDraftDirty(false);
  }

  const currentTitle = showJson
    ? "JSON-Editor"
    : activeKey
      ? formatSectionTitle(activeKey)
      : "Alle Einstellungen";

  const currentDescription = showJson
    ? "Direkte Bearbeitung der gesamten Konfiguration als validierbares JSON."
    : activeKey
      ? getSectionDescription(activeKey)
      : "Validierte fachliche und technische Konfiguration des Kernschmied-Systems.";

  return (
    <div className="flex min-h-full flex-col">
      <header
        className={[
          "sticky top-0 z-10 shrink-0",
          "border-b border-slate-200 bg-white/95",
          "px-5 py-4 backdrop-blur",
          "dark:border-white/10 dark:bg-slate-950/90",
        ].join(" ")}
      >
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="truncate text-lg font-semibold text-slate-950 dark:text-white">
                {currentTitle}
              </h2>

              {revision !== null ? (
                <StatusBadge variant="neutral">Revision {revision}</StatusBadge>
              ) : null}

              {isDirty ? (
                <StatusBadge variant="warning">Nicht gespeichert</StatusBadge>
              ) : (
                <StatusBadge variant="success">Gespeichert</StatusBadge>
              )}

              {showJson && isJsonDraftDirty ? (
                <StatusBadge variant="warning">
                  JSON noch nicht übernommen
                </StatusBadge>
              ) : null}
            </div>

            <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-400">
              {currentDescription}
            </p>

            {!showJson ? (
              <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                <span>
                  {activeKey === null
                    ? `${totalSettingCount} Werte insgesamt`
                    : `${countConfigValues(values[activeKey])} Werte in diesem Bereich`}
                </span>

                {normalizedSearchQuery ? (
                  <>
                    <span aria-hidden="true">·</span>

                    <span>{visibleSettingCount} passende Werte</span>
                  </>
                ) : null}
              </div>
            ) : null}
          </div>

          <div className="flex shrink-0 flex-wrap items-center gap-2">
            <label className="inline-flex items-center gap-2 rounded border border-slate-200 bg-slate-50 px-3 py-1 text-sm text-slate-700 dark:border-white/10 dark:bg-slate-900/40">
              <input
                type="checkbox"
                checked={
                  (values as any)?.ui?.autosave_enabled === undefined
                    ? true
                    : Boolean((values as any).ui.autosave_enabled)
                }
                onChange={(e) => {
                  setValues(
                    updateConfigValue(
                      values,
                      ["ui", "autosave_enabled"],
                      e.target.checked,
                    ),
                  );
                }}
              />

              <span className="select-none">Autosave</span>
            </label>
            <button
              type="button"
              className={secondaryButtonClassName}
              disabled={isSaving}
              onClick={handleReload}
            >
              <RefreshCw
                size={15}
                aria-hidden="true"
                className={isLoading ? "animate-spin" : undefined}
              />

              <span>Neu laden</span>
            </button>

            <button
              type="button"
              className={secondaryButtonClassName}
              disabled={!isDirty || isSaving}
              onClick={handleReset}
            >
              <RotateCcw size={15} aria-hidden="true" />

              <span>Verwerfen</span>
            </button>

            <button
              type="button"
              className={primaryButtonClassName}
              disabled={!isDirty || isSaving}
              onClick={handleSave}
            >
              <Save size={15} aria-hidden="true" />

              <span>{isSaving ? "Speichern …" : "Speichern"}</span>
            </button>
          </div>
        </div>

        {!showJson ? (
          <SettingsSearch
            value={searchQuery}
            resultCount={
              normalizedSearchQuery ? visibleSettingCount : undefined
            }
            onChange={setSearchQuery}
            onClear={() => {
              setSearchQuery("");
            }}
          />
        ) : null}
      </header>

      {error ? (
        <div className="mx-5 mt-5">
          <SettingsErrorMessage
            code={error.code}
            message={error.message}
            requestId={error.requestId}
            onRetry={handleReload}
          />
        </div>
      ) : null}

      <div className="flex-1 p-5 md:p-8">
        {showJson ? (
          <SettingsJsonEditor
            value={jsonDraft}
            error={jsonError}
            disabled={isSaving}
            isDirty={isJsonDraftDirty}
            copied={jsonCopied}
            onChange={handleJsonDraftChange}
            onApply={handleApplyJson}
            onFormat={handleFormatJson}
            onReset={handleResetJsonDraft}
            onCopy={() => {
              void handleCopyJson();
            }}
          />
        ) : activeKey === null ? (
          <SettingsForm
            entries={visibleSectionEntries}
            disabled={isSaving}
            searchQuery={normalizedSearchQuery}
            totalEntryCount={sectionEntries.length}
            onChange={handleFieldChange}
            valuesByFullKey={valuesByFullKey}
          entriesByFullKey={entriesByFullKey ?? null}
          />
        ) : (
          <SettingsSingleSection
            sectionKey={activeKey}
            value={values[activeKey]}
            disabled={isSaving}
            searchQuery={normalizedSearchQuery}
            onChange={handleFieldChange}
          />
        )}
      </div>
    </div>
  );
}

function SettingsSearch({
  value,
  resultCount,
  onChange,
  onClear,
}: {
  value: string;
  resultCount?: number;
  onChange: (value: string) => void;
  onClear: () => void;
}) {
  return (
    <div className="mt-4 flex max-w-2xl items-center gap-2">
      <div className="relative min-w-0 flex-1">
        <Search
          size={16}
          aria-hidden="true"
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
        />

        <input
          type="search"
          value={value}
          placeholder="Einstellungen durchsuchen …"
          aria-label="Einstellungen durchsuchen"
          className={[
            "block w-full rounded-lg border border-slate-300",
            "bg-white py-2 pl-9 pr-10 text-sm text-slate-900",
            "outline-none transition",
            "placeholder:text-slate-400",
            "focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20",
            "dark:border-white/10 dark:bg-slate-900 dark:text-white",
          ].join(" ")}
          onChange={(event) => {
            onChange(event.target.value);
          }}
        />

        {value ? (
          <button
            type="button"
            className={[
              "absolute right-1.5 top-1/2 inline-flex h-7 w-7",
              "-translate-y-1/2 items-center justify-center rounded-md",
              "text-slate-400 transition hover:bg-slate-100 hover:text-slate-700",
              "dark:hover:bg-white/10 dark:hover:text-white",
            ].join(" ")}
            aria-label="Suche löschen"
            onClick={onClear}
          >
            <X size={15} aria-hidden="true" />
          </button>
        ) : null}
      </div>

      {resultCount !== undefined ? (
        <span className="shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 dark:bg-white/10 dark:text-slate-300">
          {resultCount}
        </span>
      ) : null}
    </div>
  );
}

function SettingsForm({
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
  entriesByFullKey?: Record<string, any> | null;
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
        />
      ))}
    </div>
  );
}

function SettingsSingleSection({
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
  entriesByFullKey?: Record<string, any> | null;
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
}: SettingsSectionProps & {
  valuesByFullKey?: Record<string, ConfigValue> | null;
  entriesByFullKey?: Record<string, any> | null;
}) {
  const currentPath = [...path, sectionKey];

  const label = formatSettingLabel(sectionKey);

  if (depth > MAX_RENDER_DEPTH) {
    return (
      <SettingsField
        fieldKey={sectionKey}
        label={label}
        value={value}
        path={currentPath}
        disabled={disabled}
        description="Die maximale Darstellungstiefe wurde erreicht. Der Wert kann als JSON bearbeitet werden."
        valuesByFullKey={valuesByFullKey}
        onChange={onChange}
      />
    );
  }

    if (!isConfigRecord(value)) {
    if (searchQuery && !matchesSearchQuery(sectionKey, value, searchQuery)) {
      return null;
    }

    const fullKey = currentPath.join(".");

    const entry = entriesByFullKey ? entriesByFullKey[fullKey] : undefined;

    if (entry) {
      return (
        <SettingsField
          entry={entry}
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

    return (
      <SettingsField
        fieldKey={sectionKey}
        label={label}
        value={value}
        path={currentPath}
        disabled={disabled}
        description={metadata.description}
        sensitive={metadata.sensitive}
        readOnly={metadata.readOnly}
        required={metadata.required}
        placeholder={metadata.placeholder}
        minimum={metadata.minimum}
        maximum={metadata.maximum}
        step={metadata.step}
        options={metadata.options}
        valuesByFullKey={valuesByFullKey}
        onChange={onChange}
      />
    );
  }

  const visibleEntries = Object.entries(value)
    .filter(([childKey, childValue]) =>
      matchesSearchQuery(childKey, childValue, searchQuery),
    )
    .sort((left, right) =>
      formatSettingLabel(left[0]).localeCompare(
        formatSettingLabel(right[0]),
        "de",
        {
          sensitivity: "base",
        },
      ),
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
        "overflow-hidden rounded-2xl border border-slate-200",
        "bg-slate-100/60",
        "dark:border-white/10 dark:bg-white/3",
      ].join(" ")}
    >
      <header
        className={[
          "border-b border-slate-200 bg-white px-5 py-4",
          "dark:border-white/10 dark:bg-slate-900/60",
        ].join(" ")}
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-semibold text-slate-950 dark:text-white">
              {label}
            </h2>

            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {getSectionDescription(sectionKey)}
            </p>
          </div>

          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 dark:bg-white/10 dark:text-slate-300">
            {countConfigValues(value)} Werte
          </span>
        </div>

        <code className="mt-3 inline-block rounded bg-slate-100 px-2 py-1 text-xs text-slate-500 dark:bg-white/5 dark:text-slate-400">
          {currentPath.join(".")}
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

function SettingsJsonEditor({
  value,
  error,
  disabled,
  isDirty,
  copied,
  onChange,
  onApply,
  onFormat,
  onReset,
  onCopy,
}: {
  value: string;
  error: string | null;
  disabled: boolean;
  isDirty: boolean;
  copied: boolean;
  onChange: (value: string) => void;
  onApply: () => void;
  onFormat: () => void;
  onReset: () => void;
  onCopy: () => void;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-slate-900/50">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="font-semibold text-slate-950 dark:text-white">
              JSON-Konfiguration
            </h2>

            {isDirty ? (
              <StatusBadge variant="warning">Bearbeitet</StatusBadge>
            ) : null}
          </div>

          <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
            Es werden ausschließlich gültige Kernschmied-Konfigurationswerte
            übernommen. Zusätzliche Felder können vom Backend abgelehnt werden.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className={secondaryButtonClassName}
            disabled={disabled}
            onClick={onCopy}
          >
            {copied ? (
              <Check size={15} aria-hidden="true" />
            ) : (
              <Clipboard size={15} aria-hidden="true" />
            )}

            <span>{copied ? "Kopiert" : "Kopieren"}</span>
          </button>

          <button
            type="button"
            className={secondaryButtonClassName}
            disabled={disabled}
            onClick={onFormat}
          >
            Formatieren
          </button>

          <button
            type="button"
            className={secondaryButtonClassName}
            disabled={disabled || !isDirty}
            onClick={onReset}
          >
            Zurücksetzen
          </button>

          <button
            type="button"
            className={primaryButtonClassName}
            disabled={disabled || !isDirty}
            onClick={onApply}
          >
            JSON übernehmen
          </button>
        </div>
      </div>

      <textarea
        rows={30}
        value={value}
        disabled={disabled}
        spellCheck={false}
        aria-label="JSON-Konfiguration"
        aria-invalid={error !== null}
        aria-describedby={error ? "settings-json-error" : "settings-json-help"}
        className={[
          "mt-5 block w-full resize-y rounded-xl border",
          error ? "border-red-400" : "border-slate-300",
          "bg-slate-950 p-4 font-mono text-sm leading-6 text-slate-100",
          "outline-none transition",
          "focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20",
          "disabled:cursor-not-allowed disabled:opacity-60",
          "dark:border-white/10",
        ].join(" ")}
        onChange={(event) => {
          onChange(event.target.value);
        }}
      />

      <p
        id="settings-json-help"
        className="mt-3 text-xs text-slate-500 dark:text-slate-400"
      >
        Änderungen werden erst nach „JSON übernehmen“ in den lokalen
        Konfigurationsentwurf übernommen. Das Speichern erfolgt anschließend
        über die Hauptaktion „Speichern“.
      </p>

      {error ? (
        <p
          id="settings-json-error"
          className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300"
          role="alert"
        >
          {error}
        </p>
      ) : null}
    </section>
  );
}

function SettingsErrorMessage({
  code,
  message,
  requestId,
  onRetry,
}: {
  code: string;
  message: string;
  requestId?: string;
  onRetry: () => void;
}) {
  return (
    <div
      className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-900 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-200"
      role="alert"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-semibold">Konfigurationsfehler</p>

          <p className="mt-1 text-sm leading-6">{message}</p>

          <dl className="mt-3 grid gap-1 text-xs opacity-80">
            <div className="flex gap-2">
              <dt className="font-medium">Code:</dt>

              <dd className="font-mono">{code}</dd>
            </div>

            {requestId ? (
              <div className="flex gap-2">
                <dt className="font-medium">Anfrage-ID:</dt>

                <dd className="font-mono">{requestId}</dd>
              </div>
            ) : null}
          </dl>
        </div>

        <button
          type="button"
          className={secondaryButtonClassName}
          onClick={onRetry}
        >
          <RefreshCw size={15} aria-hidden="true" />
          Erneut laden
        </button>
      </div>
    </div>
  );
}

function SettingsLoadingState() {
  return (
    <div
      className="flex min-h-0 flex-1 items-center justify-center bg-slate-50 p-8 dark:bg-slate-950/30"
      aria-busy="true"
      aria-live="polite"
    >
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white px-6 py-5 shadow-sm dark:border-white/10 dark:bg-slate-900/60">
        <div className="flex items-center gap-3">
          <span
            className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600"
            aria-hidden="true"
          />

          <div>
            <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Einstellungen werden geladen …
            </p>

            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Konfiguration und Revision werden vom Backend abgerufen.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function SettingsEmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center dark:border-white/15 dark:bg-slate-900/40">
      <h3 className="font-semibold text-slate-900 dark:text-white">{title}</h3>

      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500 dark:text-slate-400">
        {description}
      </p>
    </div>
  );
}

function StatusBadge({
  variant,
  children,
}: {
  variant: "neutral" | "success" | "warning";
  children: ReactNode;
}) {
  const variantClassName =
    variant === "success"
      ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300"
      : variant === "warning"
        ? "bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300"
        : "bg-slate-100 text-slate-600 dark:bg-white/10 dark:text-slate-300";

  return (
    <span
      className={[
        "rounded-full px-2.5 py-1 text-xs font-medium",
        variantClassName,
      ].join(" ")}
    >
      {children}
    </span>
  );
}

function updateConfigValue(
  source: ConfigObject,
  path: string[],
  value: ConfigValue,
): ConfigObject {
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

  const nestedSource: ConfigObject = isConfigRecord(currentValue)
    ? currentValue
    : {};

  return {
    ...source,
    [currentKey]: updateConfigValue(nestedSource, remainingPath, value),
  };
}

function formatSettingLabel(value: string): string {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatSectionTitle(key: string): string {
  return formatSettingLabel(key);
}

function getSectionDescription(key: string): string {
  const normalizedKey = key.toLocaleLowerCase("de");

  const descriptions: Record<string, string> = {
    identity:
      "Identität, Grundauftrag und allgemeines Verhalten von Kernschmied.",
    behavior: "Kommunikationsverhalten, Autonomie und Selbstprüfung.",
    prompts: "Versionierte System- und Aufgabenprompts sowie deren Vererbung.",
    models: "Modelle, Auswahlregeln und Generierungsparameter.",
    providers: "Verbindungen, Timeouts und Laufzeitwerte der Modellprovider.",
    tools: "Tool-Auswahl, Ausführungsgrenzen und Bestätigungspflichten.",
    knowledge: "Wissensquellen, Gedächtnis und Kontextauswahl.",
    context: "Kontextgrenzen, Quellenprioritäten und Relevanzregeln.",
    workflow: "Planung, Ausführung, Selbstprüfung und Abschluss von Aufgaben.",
    runtime: "Globale Laufzeitgrenzen und operative Systemwerte.",
    storage: "Speicherziele, Versionierung und Aufbewahrung.",
    communication: "Kommunikationskanäle und Interaktionsverhalten.",
    appearance: "Darstellung, Theme und lokale Oberflächenpräferenzen.",
    security: "Sicherheitsgrenzen, Autorisierung und Bestätigungspflichten.",
    diagnostics: "Diagnose-, Qualitäts- und Laufzeitinformationen.",
    learning: "Lernkandidaten, Bewertung und kontrollierte Optimierung.",
  };

  return (
    descriptions[normalizedKey] ??
    `Konfigurationsbereich „${formatSettingLabel(key)}“.`
  );
}

function inferFieldMetadata({
  fieldKey,
  path,
  value,
}: {
  fieldKey: string;
  path: string[];
  value: ConfigValue;
}): InferredFieldMetadata {
  const normalizedKey = fieldKey.toLocaleLowerCase("de");

  const normalizedPath = path.join(".").toLocaleLowerCase("de");

  const metadata: InferredFieldMetadata = {};

  if (
    includesAny(normalizedKey, [
      "secret",
      "password",
      "passwort",
      "token",
      "api_key",
      "apikey",
      "credential",
    ])
  ) {
    metadata.sensitive = true;

    metadata.description =
      "Sensible Werte sollten als Secret-Referenz und nicht als Klartext gespeichert werden.";
  }

  if (
    includesAny(normalizedKey, [
      "description",
      "beschreibung",
      "prompt",
      "instruction",
      "anweisung",
    ])
  ) {
    metadata.description ??=
      "Mehrzeiliger Textwert für die dynamische Laufzeitkonfiguration.";
  }

  if (normalizedKey === "timezone" || normalizedKey === "time_zone") {
    metadata.placeholder = "Europe/Berlin";

    metadata.required = true;
  }

  if (normalizedKey === "language" || normalizedKey === "locale") {
    metadata.options = [
      {
        value: "de",
        label: "Deutsch",
      },
      {
        value: "en",
        label: "Englisch",
      },
    ];
  }

  if (normalizedKey === "theme") {
    metadata.options = [
      {
        value: "system",
        label: "System",
      },
      {
        value: "light",
        label: "Hell",
      },
      {
        value: "dark",
        label: "Dunkel",
      },
    ];
  }

  if (normalizedKey === "environment") {
    metadata.options = [
      {
        value: "development",
        label: "Development",
      },
      {
        value: "intranet",
        label: "Intranet",
      },
      {
        value: "internet",
        label: "Internet",
      },
    ];
  }

  if (normalizedKey === "autonomy_level" || normalizedKey === "autonomy") {
    metadata.options = [
      {
        value: "advisory",
        label: "Nur beraten",
      },
      {
        value: "draft",
        label: "Entwürfe erstellen",
      },
      {
        value: "prepare",
        label: "Änderungen vorbereiten",
      },
      {
        value: "execute_approved",
        label: "Freigegebene Aktionen ausführen",
      },
    ];
  }

  if (includesAny(normalizedKey, ["temperature", "top_p", "min_p"])) {
    metadata.minimum = 0;

    metadata.maximum = normalizedKey === "temperature" ? 2 : 1;

    metadata.step = 0.01;
  }

  if (
    includesAny(normalizedKey, ["timeout", "duration"]) &&
    typeof value === "number"
  ) {
    metadata.minimum = 0;

    metadata.step = 1;
  }

  if (
    includesAny(normalizedKey, [
      "max_",
      "limit",
      "count",
      "retries",
      "rounds",
      "steps",
    ]) &&
    typeof value === "number"
  ) {
    metadata.minimum ??= 0;

    metadata.step ??= 1;
  }

  if (
    includesAny(normalizedPath, [
      "revision",
      "status",
      "health",
      "latency",
      "error_rate",
      "registry_revision",
    ])
  ) {
    metadata.readOnly = true;

    metadata.description ??=
      "Dieser Wert wird vom Backend ermittelt und ist in dieser Ansicht schreibgeschützt.";
  }

  if (includesAny(normalizedKey, ["endpoint", "base_url", "url", "webhook"])) {
    metadata.placeholder = "https://example.org";
  }

  return metadata;
}

function matchesSearchQuery(
  key: string,
  value: ConfigValue | undefined,
  searchQuery: string,
): boolean {
  if (!searchQuery) {
    return true;
  }

  if (normalizeText(key).includes(searchQuery)) {
    return true;
  }

  if (value === undefined) {
    return false;
  }

  if (typeof value === "string") {
    return normalizeText(value).includes(searchQuery);
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value).toLocaleLowerCase("de").includes(searchQuery);
  }

  if (value === null) {
    return false;
  }

  if (Array.isArray(value)) {
    return value.some((item, index) =>
      matchesSearchQuery(String(index), item, searchQuery),
    );
  }

  return Object.entries(value).some(([childKey, childValue]) =>
    matchesSearchQuery(childKey, childValue, searchQuery),
  );
}

function normalizeText(value: string): string {
  return value.replace(/[_-]+/g, " ").toLocaleLowerCase("de");
}

function countConfigValues(
  value: ConfigValue | ConfigObject | undefined,
): number {
  if (value === undefined) {
    return 0;
  }

  if (
    value === null ||
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return 1;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return 1;
    }

    return value.reduce<number>(
      (count, item) => count + countConfigValues(item),
      0,
    );
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
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return false;
  }

  return Object.values(value).every(isConfigValue);
}

function isConfigRecord(value: ConfigValue | undefined): value is ConfigObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isConfigValue(value: unknown): value is ConfigValue {
  if (
    value === null ||
    typeof value === "string" ||
    typeof value === "boolean"
  ) {
    return true;
  }

  if (typeof value === "number") {
    return Number.isFinite(value);
  }

  if (Array.isArray(value)) {
    return value.every(isConfigValue);
  }

  return isConfigObject(value);
}

type ConfigParseResult =
  | {
      ok: true;
      value: ConfigObject;
    }
  | {
      ok: false;
      error: string;
    };

function parseConfigObject(source: string): ConfigParseResult {
  if (source.trim() === "") {
    return {
      ok: false,
      error: "Die JSON-Konfiguration darf nicht leer sein.",
    };
  }

  let parsed: unknown;

  try {
    parsed = JSON.parse(source) as unknown;
  } catch {
    return {
      ok: false,
      error: "Die JSON-Eingabe ist syntaktisch ungültig.",
    };
  }

  if (!isConfigObject(parsed)) {
    return {
      ok: false,
      error:
        "Die JSON-Eingabe muss ein Objekt mit gültigen Konfigurationswerten sein.",
    };
  }

  return {
    ok: true,
    value: parsed,
  };
}

function includesAny(value: string, candidates: string[]): boolean {
  return candidates.some((candidate) => value.includes(candidate));
}

const secondaryButtonClassName = [
  "inline-flex items-center justify-center gap-2 rounded-lg",
  "border border-slate-300 bg-white px-3.5 py-2",
  "text-sm font-medium text-slate-700 transition",
  "hover:bg-slate-50",
  "focus-visible:outline-none focus-visible:ring-2",
  "focus-visible:ring-blue-500 focus-visible:ring-offset-2",
  "disabled:cursor-not-allowed disabled:opacity-50",
  "dark:border-white/10 dark:bg-white/5 dark:text-slate-200",
  "dark:hover:bg-white/10 dark:focus-visible:ring-offset-slate-950",
].join(" ");

const primaryButtonClassName = [
  "inline-flex items-center justify-center gap-2 rounded-lg",
  "bg-blue-600 px-4 py-2 text-sm font-medium text-white",
  "transition hover:bg-blue-700",
  "focus-visible:outline-none focus-visible:ring-2",
  "focus-visible:ring-blue-500 focus-visible:ring-offset-2",
  "disabled:cursor-not-allowed disabled:opacity-50",
  "dark:focus-visible:ring-offset-slate-950",
].join(" ");
