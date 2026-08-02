import type { ConfigValue } from '../../contracts/config';

export interface SettingsFieldOption {
  value: string | number | boolean;
  label: string;
  description?: string;
}

export interface InferredFieldMetadata {
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

export function includesAny(value: string, candidates: string[]): boolean {
  return candidates.some((candidate) => value.includes(candidate));
}

export function inferFieldMetadata({
  fieldKey,
  path,
  value,
}: {
  fieldKey: string;
  path: string[];
  value: ConfigValue;
}): InferredFieldMetadata {
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

export default inferFieldMetadata;
