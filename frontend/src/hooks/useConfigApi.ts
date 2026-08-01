import { useEffect, useState } from "react";

import type { ConfigValue } from "../contracts/config";

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

  if (!spec.endpoint.startsWith("/api/")) return null;

  let url = spec.endpoint;

  // If dependency is defined, append as query parameter
  if (spec.depends_on && spec.dependency_parameter && valuesByFullKey) {
    const depValue = valuesByFullKey[spec.depends_on];

    if (depValue === undefined || depValue === null) return null;

    const qp = `${encodeURIComponent(spec.dependency_parameter)}=${encodeURIComponent(String(depValue))}`;

    url += url.includes("?") ? `&${qp}` : `?${qp}`;
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

        let items: any[] = [];

        if (Array.isArray(data)) items = data;
        else if (Array.isArray((data as any).items))
          items = (data as any).items;
        else if (Array.isArray((data as any).providers))
          items = (data as any).providers;
        else items = [];

        const mapped = items.map((it) => {
          if (it && typeof it === "object") {
            const value =
              it.value ??
              it.id ??
              it.model_id ??
              it.provider_id ??
              it.name ??
              JSON.stringify(it);
            const label =
              it.label ?? it.name ?? it.display_name ?? String(value);
            return { value, label } as SettingsFieldOption;
          }

          return { value: it, label: String(it) } as SettingsFieldOption;
        });

        setOptions(mapped);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err.name === "AbortError") return;
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
