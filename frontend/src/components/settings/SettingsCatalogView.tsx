import { useEffect, useMemo, useState } from "react";

import { fetchSettingsCatalog } from "../../api/settingsCatalog";
import type {
  SettingsAvailability,
  SettingsCatalogResponse,
  SettingsFieldDescriptor,
  SettingsGroupDescriptor,
} from "../../contracts/settings";

const badgeLabel: Record<SettingsAvailability, string> = {
  available: "Erreichbar",
  prepared: "Vorbereitet",
  planned: "Geplant",
};

function FieldCard({ field }: { field: SettingsFieldDescriptor }) {
  const target = field.endpoint ??
    (field.config_group && field.config_key
      ? `/api/v1/config/${field.config_group}/${field.config_key}`
      : undefined);

  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h4 className="font-semibold text-slate-900 dark:text-slate-100">{field.title}</h4>
          {field.description ? (
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{field.description}</p>
          ) : null}
        </div>
        <span className="rounded-full border px-2 py-1 text-xs font-medium">
          {badgeLabel[field.availability]}
        </span>
      </div>

      <dl className="mt-3 grid gap-2 text-xs text-slate-500 sm:grid-cols-2 dark:text-slate-400">
        <div><dt className="font-medium">Quelle</dt><dd>{field.source}</dd></div>
        <div><dt className="font-medium">Darstellung</dt><dd>{field.control}</dd></div>
        {target ? <div className="sm:col-span-2"><dt className="font-medium">API</dt><dd className="break-all font-mono">{target}</dd></div> : null}
      </dl>

      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        {field.editable ? <span className="rounded bg-emerald-100 px-2 py-1 text-emerald-800">editierbar</span> : null}
        {field.requires_confirmation ? <span className="rounded bg-amber-100 px-2 py-1 text-amber-800">Bestätigung</span> : null}
        {field.sensitive ? <span className="rounded bg-rose-100 px-2 py-1 text-rose-800">sensibel</span> : null}
      </div>
    </article>
  );
}

function GroupPanel({ group }: { group: SettingsGroupDescriptor }) {
  return (
    <section className="space-y-6">
      <header>
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="text-2xl font-bold text-slate-950 dark:text-white">{group.title}</h2>
          <span className="rounded-full border px-2 py-1 text-xs">{badgeLabel[group.availability]}</span>
        </div>
        <p className="mt-2 max-w-3xl text-slate-600 dark:text-slate-300">{group.description}</p>
      </header>

      {group.sections
        .slice()
        .sort((a, b) => a.order - b.order)
        .map((section) => (
          <div key={section.id} className="space-y-3">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{section.title}</h3>
            <div className="grid gap-3 xl:grid-cols-2">
              {section.fields
                .slice()
                .sort((a, b) => a.order - b.order)
                .map((field) => <FieldCard key={field.id} field={field} />)}
            </div>
          </div>
        ))}
    </section>
  );
}

export function SettingsCatalogView() {
  const [catalog, setCatalog] = useState<SettingsCatalogResponse | null>(null);
  const [selectedGroupId, setSelectedGroupId] = useState<string>("identity");
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    void fetchSettingsCatalog(controller.signal)
      .then((value) => {
        setCatalog(value);
        if (value.groups.length > 0) {
          setSelectedGroupId((current) =>
            value.groups.some((group) => group.id === current) ? current : value.groups[0].id,
          );
        }
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "Unbekannter Fehler beim Laden.");
      });
    return () => controller.abort();
  }, []);

  const groups = useMemo(() => {
    const source = catalog?.groups ?? [];
    const normalizedQuery = query.trim().toLocaleLowerCase("de");
    if (!normalizedQuery) return source.slice().sort((a, b) => a.order - b.order);
    return source.filter((group) => {
      const values = [group.title, group.description, ...group.sections.flatMap((section) => [section.title, ...section.fields.flatMap((field) => [field.title, field.description ?? ""])])];
      return values.some((value) => value.toLocaleLowerCase("de").includes(normalizedQuery));
    });
  }, [catalog, query]);

  const selectedGroup = groups.find((group) => group.id === selectedGroupId) ?? groups[0];

  if (error) return <div className="rounded-xl border border-red-300 bg-red-50 p-5 text-red-800">{error}</div>;
  if (!catalog) return <div className="p-8 text-slate-600">Settings-Katalog wird geladen …</div>;

  return (
    <div className="grid min-h-0 gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
      <aside className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <div>
          <h1 className="text-xl font-bold text-slate-950 dark:text-white">Einstellungen</h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Werte, Ressourcen und Laufzeitstatus klar getrennt.</p>
        </div>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Einstellungen durchsuchen"
          className="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm dark:border-slate-600"
        />
        <nav className="space-y-1">
          {groups.map((group) => (
            <button
              key={group.id}
              type="button"
              onClick={() => setSelectedGroupId(group.id)}
              className={`w-full rounded-lg px-3 py-2 text-left text-sm transition ${selectedGroup?.id === group.id ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-950" : "hover:bg-slate-100 dark:hover:bg-slate-800"}`}
            >
              <span className="font-medium">{group.title}</span>
              <span className="mt-1 block text-xs opacity-70">{badgeLabel[group.availability]}</span>
            </button>
          ))}
        </nav>
      </aside>
      <main className="min-w-0 overflow-auto rounded-2xl border border-slate-200 bg-slate-50 p-6 dark:border-slate-700 dark:bg-slate-950">
        {selectedGroup ? <GroupPanel group={selectedGroup} /> : <p>Keine Einstellungen gefunden.</p>}
      </main>
    </div>
  );
}
