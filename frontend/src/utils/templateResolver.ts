export interface TemplateProviders {
  system?: {
    name?: string;
    date?: string;
    time?: string;
    [k: string]: unknown;
  };
  user?: {
    name?: string;
    id?: string;
    [k: string]: unknown;
  };
  [k: string]: unknown;
}

export function resolveTemplate(template: string | null | undefined, providers: TemplateProviders = {}): string {
  if (!template) return '';

  const now = new Date();
  const defaults = {
    system: {
      name: providers.system?.name ?? 'System',
      date: providers.system?.date ?? now.toLocaleDateString(),
      time: providers.system?.time ?? now.toLocaleTimeString(),
    },
    user: {
      name: providers.user?.name ?? 'Benutzer',
      id: providers.user?.id ?? '',
    },
  } as TemplateProviders;

  // Simple replacement for well-known placeholders
  let out = String(template);

  out = out.replace(/\{\{\s*system\.date\s*\}\}/gi, String(defaults.system!.date));
  out = out.replace(/\{\{\s*system\.time\s*\}\}/gi, String(defaults.system!.time));
  out = out.replace(/\{\{\s*system\.name\s*\}\}/gi, String(defaults.system!.name));

  out = out.replace(/\{\{\s*user\.name\s*\}\}/gi, String(defaults.user!.name));
  out = out.replace(/\{\{\s*user\.id\s*\}\}/gi, String(defaults.user!.id));

  // Fallback: simple {{key}} flattening from providers
  out = out.replace(/\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}/g, (_, key) => {
    const parts = key.split('.');
    let cur: any = providers as any;
    for (const p of parts) {
      if (cur && typeof cur === 'object' && p in cur) cur = cur[p];
      else {
        // try defaults
        cur = (defaults as any)[parts[0]] ? (defaults as any)[parts[0]][parts[1]] : undefined;
        break;
      }
    }
    return cur === undefined || cur === null ? '' : String(cur);
  });

  return out;
}
