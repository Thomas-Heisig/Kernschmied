// F:\Kernschmied\frontend\src\components\settings\SettingsContent.tsx

import { useState } from "react";
import type { ConfigValue } from "../../contracts/config";
import type { UseSystemConfigReturn } from "../../hooks/useSystemConfig";
import { SettingsField } from "./SettingsField";

interface SettingsContentProps {
  activeKey: string | null;
  showJson: boolean;
  config: UseSystemConfigReturn;
}

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

  if (isLoading) {
    return <SettingsLoadingState />;
  }

  if (showJson && jsonDraft === "") {
    setJsonDraft(JSON.stringify(values, null, 2));
  }

  function handleApplyJson() {
    try {
      const parsed = JSON.parse(jsonDraft);
      if (!isConfigObject(parsed)) {
        setJsonError(
          "Die JSON-Eingabe muss ein Objekt mit gültigen Konfigurationswerten sein.",
        );
        return;
      }
      setValues(parsed);
      setJsonError(null);
    } catch {
      setJsonError("Die JSON-Eingabe ist syntaktisch ungültig.");
    }
  }

  function handleFieldChange(path: string[], value: ConfigValue) {
    setValues(updateConfigValue(values, path, value));
  }

  return (
    <div className="flex min-h-full flex-col">
      {/* Toolbar – Titelgewicht reduziert */}
      <header className="sticky top-0 z-10 shrink-0 border-b border-slate-200 bg-white/90 px-5 py-4 backdrop-blur dark:border-white/10 dark:bg-slate-950/80">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-lg font-medium text-slate-950 dark:text-white">
                {activeKey
                  ? formatSectionTitle(activeKey)
                  : showJson
                    ? "JSON-Editor"
                    : "Alle Einstellungen"}
              </h2>
              {revision !== null && (
                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 dark:bg-white/10 dark:text-slate-300">
                  Revision {revision}
                </span>
              )}
              {isDirty ? (
                <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-800 dark:bg-amber-500/15 dark:text-amber-300">
                  Nicht gespeichert
                </span>
              ) : (
                <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300">
                  Gespeichert
                </span>
              )}
            </div>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
              {showJson
                ? "Direkte Bearbeitung der gesamten Konfiguration als JSON."
                : "Validierte fachliche Konfiguration des Kernschmied-Systems."}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              className={secondaryButtonClassName}
              disabled={isSaving}
              onClick={() => reload()}
            >
              Neu laden
            </button>
            <button
              type="button"
              className={secondaryButtonClassName}
              disabled={!isDirty || isSaving}
              onClick={reset}
            >
              Verwerfen
            </button>
            <button
              type="button"
              className={primaryButtonClassName}
              disabled={!isDirty || isSaving}
              onClick={() => save()}
            >
              {isSaving ? "Speichern …" : "Speichern"}
            </button>
          </div>
        </div>
      </header>

      {error && (
        <div className="mx-5 mt-5">
          <SettingsErrorMessage
            code={error.code}
            message={error.message}
            requestId={error.requestId}
          />
        </div>
      )}

      <div className="flex-1 p-5 md:p-8">
        {showJson ? (
          <SettingsJsonEditor
            value={jsonDraft}
            error={jsonError}
            disabled={isSaving}
            onChange={setJsonDraft}
            onApply={handleApplyJson}
          />
        ) : activeKey === null ? (
          <SettingsForm
            entries={Object.entries(values)}
            disabled={isSaving}
            onChange={handleFieldChange}
          />
        ) : (
          <SettingsSingleSection
            sectionKey={activeKey}
            value={values[activeKey]}
            disabled={isSaving}
            onChange={handleFieldChange}
          />
        )}
      </div>
    </div>
  );
}

// ----- Unterkomponenten (Schriftgewicht reduziert) -----

function SettingsForm({
  entries,
  disabled,
  onChange,
}: {
  entries: [string, ConfigValue][];
  disabled: boolean;
  onChange: (path: string[], value: ConfigValue) => void;
}) {
  if (entries.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center dark:border-white/15 dark:bg-slate-900/40">
        <h3 className="font-medium text-slate-900 dark:text-white">
          Keine Einstellungen vorhanden
        </h3>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Der Server hat derzeit keine fachliche Konfiguration ausgeliefert.
        </p>
      </div>
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
          onChange={onChange}
        />
      ))}
    </div>
  );
}

function SettingsSingleSection({
  sectionKey,
  value,
  disabled,
  onChange,
}: {
  sectionKey: string;
  value: ConfigValue;
  disabled: boolean;
  onChange: (path: string[], value: ConfigValue) => void;
}) {
  if (value === undefined || value === null) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center dark:border-white/15 dark:bg-slate-900/40">
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Diese Kategorie enthält keine Einstellungen.
        </p>
      </div>
    );
  }

  return (
    <SettingsSection
      sectionKey={sectionKey}
      value={value}
      disabled={disabled}
      onChange={onChange}
    />
  );
}

function SettingsSection({
  sectionKey,
  value,
  disabled,
  onChange,
}: {
  sectionKey: string;
  value: ConfigValue;
  disabled: boolean;
  onChange: (path: string[], value: ConfigValue) => void;
}) {
  const label = formatSettingLabel(sectionKey);

  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return (
      <SettingsField
        fieldKey={sectionKey}
        label={label}
        value={value}
        path={[sectionKey]}
        disabled={disabled}
        onChange={onChange}
      />
    );
  }

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-slate-100/60 dark:border-white/10 dark:bg-white/3">
      <header className="border-b border-slate-200 bg-white px-5 py-4 dark:border-white/10 dark:bg-slate-900/60">
        <h2 className="font-medium text-slate-950 dark:text-white">{label}</h2>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Konfigurationsbereich: {sectionKey}
        </p>
      </header>
      <div className="grid gap-4 p-4 md:grid-cols-2">
        {Object.entries(value as Record<string, ConfigValue>).map(
          ([fieldKey, fieldValue]) => (
            <SettingsField
              key={fieldKey}
              fieldKey={fieldKey}
              label={formatSettingLabel(fieldKey)}
              value={fieldValue}
              path={[sectionKey, fieldKey]}
              disabled={disabled}
              onChange={onChange}
            />
          ),
        )}
      </div>
    </section>
  );
}

function SettingsJsonEditor({
  value,
  error,
  disabled,
  onChange,
  onApply,
}: {
  value: string;
  error: string | null;
  disabled: boolean;
  onChange: (value: string) => void;
  onApply: () => void;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-white/10 dark:bg-slate-900/50">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-medium text-slate-950 dark:text-white">
            JSON-Konfiguration
          </h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Nur bekannte und vom Backend validierbare Werte verwenden.
          </p>
        </div>
        <button
          type="button"
          className={primaryButtonClassName}
          disabled={disabled}
          onClick={onApply}
        >
          JSON übernehmen
        </button>
      </div>
      <textarea
        rows={28}
        value={value}
        disabled={disabled}
        spellCheck={false}
        aria-label="JSON-Konfiguration"
        className={[
          "mt-5 block w-full resize-y rounded-xl border border-slate-300",
          "bg-slate-950 p-4 font-mono text-sm leading-6 text-slate-100",
          "outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20",
          "disabled:cursor-not-allowed disabled:opacity-60",
          "dark:border-white/10",
        ].join(" ")}
        onChange={(e) => onChange(e.target.value)}
      />
      {error && (
        <p
          className="mt-3 text-sm font-medium text-red-700 dark:text-red-300"
          role="alert"
        >
          {error}
        </p>
      )}
    </section>
  );
}

function SettingsErrorMessage({
  code,
  message,
  requestId,
}: {
  code: string;
  message: string;
  requestId?: string;
}) {
  return (
    <div
      className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-900 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-200"
      role="alert"
    >
      <p className="font-medium">Konfigurationsfehler</p>
      <p className="mt-1 text-sm">{message}</p>
      <dl className="mt-3 grid gap-1 text-xs opacity-80">
        <div className="flex gap-2">
          <dt className="font-medium">Code:</dt>
          <dd className="font-mono">{code}</dd>
        </div>
        {requestId && (
          <div className="flex gap-2">
            <dt className="font-medium">Anfrage-ID:</dt>
            <dd className="font-mono">{requestId}</dd>
          </div>
        )}
      </dl>
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
      <div className="rounded-2xl border border-slate-200 bg-white px-6 py-5 shadow-sm dark:border-white/10 dark:bg-slate-900/60">
        <div className="flex items-center gap-3">
          <span
            className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600"
            aria-hidden="true"
          />
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
            Einstellungen werden geladen …
          </p>
        </div>
      </div>
    </div>
  );
}

// ----- Hilfsfunktionen -----

function updateConfigValue(source: any, path: string[], value: any): any {
  if (path.length === 0) return source;
  const [currentKey, ...remainingPath] = path;
  if (!currentKey) return source;
  if (remainingPath.length === 0) {
    return { ...source, [currentKey]: value };
  }
  const nested =
    source[currentKey] &&
    typeof source[currentKey] === "object" &&
    !Array.isArray(source[currentKey])
      ? source[currentKey]
      : {};
  return {
    ...source,
    [currentKey]: updateConfigValue(nested, remainingPath, value),
  };
}

function formatSettingLabel(value: string): string {
  return value.replace(/[_-]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatSectionTitle(key: string): string {
  return formatSettingLabel(key);
}

function isConfigObject(value: unknown): value is Record<string, any> {
  if (typeof value !== "object" || value === null || Array.isArray(value))
    return false;
  return Object.values(value).every(isConfigValue);
}

function isConfigValue(value: unknown): boolean {
  if (value === null || typeof value === "string" || typeof value === "boolean")
    return true;
  if (typeof value === "number") return Number.isFinite(value);
  if (Array.isArray(value)) return value.every(isConfigValue);
  return isConfigObject(value);
}

const secondaryButtonClassName = [
  "rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700",
  "transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50",
  "dark:border-white/10 dark:bg-white/5 dark:text-slate-200 dark:hover:bg-white/10",
].join(" ");

const primaryButtonClassName = [
  "rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition",
  "hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2",
  "disabled:cursor-not-allowed disabled:opacity-50 dark:focus-visible:ring-offset-slate-950",
].join(" ");
