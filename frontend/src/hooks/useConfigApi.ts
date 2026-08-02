import { useEffect, useState } from 'react';

import type { ConfigValue } from '../contracts/config';

export interface DynamicOptionsSpec {
  endpoint: string;
  depends_on?: string;
  dependency_parameter?: string;
}

export interface SettingsFieldOption {
  value: string | number | boolean;
  label: string;
  description?: string;
}

function buildOptionsUrl(
  spec: DynamicOptionsSpec,
  valuesByFullKey?: Record<string, ConfigValue> | null,
): string | null {
  if (!spec || !spec.endpoint) return null;

  if (!spec.endpoint.startsWith('/api/')) return null;

  let url = spec.endpoint;

  // If dependency is defined, append as query parameter
  if (spec.depends_on && spec.dependency_parameter && valuesByFullKey) {
    const depValue = valuesByFullKey[spec.depends_on];

    if (depValue === undefined || depValue === null) return null;

    const qp = `${encodeURIComponent(spec.dependency_parameter)}=${encodeURIComponent(String(depValue))}`;

    url += url.includes('?') ? `&${qp}` : `?${qp}`;
  }

  return url;
}

export function useConfigOptions(
  dynamicOptions: DynamicOptionsSpec | null | undefined,
  valuesByFullKey?: Record<string, ConfigValue> | null,
) {
  const [options, setOptions] = useState<SettingsFieldOption[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!dynamicOptions) return;

    const url = buildOptionsUrl(dynamicOptions, valuesByFullKey ?? null);

    if (!url) {
      setOptions(null);
      setError(null);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    let cancelled = false;

    setLoading(true);
    setError(null);

    fetch(url, { signal: controller.signal })
      .then((resp) => {
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        return resp.json();
      })
      .then((data) => {
        if (cancelled) return;

        // Support structured responses that include full ConfigEntryResponse items
        const extractArray = (v: unknown): unknown[] => {
          if (Array.isArray(v)) return v;
          if (v && typeof v === 'object') {
            const record = v as Record<string, unknown>;
            if (Array.isArray(record.items)) return record.items;
            if (Array.isArray(record.providers)) return record.providers;
            if (Array.isArray(record.results)) return record.results;
          }
          return [];
        };

        const items = extractArray(data);

        const mapped = items.map((it) => {
          if (it && typeof it === 'object') {
            const record = it as Record<string, unknown>;
            // If the remote endpoint returned full entries, prefer `value` and `label` fields.
            const valueCandidate =
              record.value ?? record.id ?? record.model_id ?? record.provider_id ?? record.name ?? undefined;
            const value = valueCandidate !== undefined ? valueCandidate : record;
            const labelCandidate = record.label ?? record.name ?? record.display_name ?? undefined;
            const label = labelCandidate !== undefined ? String(labelCandidate) : JSON.stringify(value);
            return { value: value as string | number | boolean, label } as SettingsFieldOption;
          }

          return { value: it as string | number | boolean, label: String(it) } as SettingsFieldOption;
        });

        setOptions(mapped);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err.name === 'AbortError') return;
        setError(String(err.message ?? err));
        setOptions([]);
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [dynamicOptions, JSON.stringify(valuesByFullKey ?? {})]);

  return { options, loading, error } as const;
}

export default useConfigOptions;
