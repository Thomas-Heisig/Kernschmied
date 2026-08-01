// F:\Kernschmied\frontend\src\contracts\hierarchy.ts

export const HIERARCHY_SCHEMA_VERSION = '1.0' as const;

export type HierarchyNodeId = string;
export type HierarchyNodeType = string;
export type HierarchyActionKind = string;

/**
 * Validierte, frei erweiterbare Metadaten eines Hierarchieknotens.
 *
 * Fachliche Daten dürfen hier abgelegt werden, sofern sie vom Backend
 * validiert wurden. Das Frontend darf aus unbekannten Metadaten keine
 * Komponenten oder Aktionen dynamisch erzeugen.
 */
export interface HierarchyNodeMetadata {
  [key: string]: unknown;
}

/**
 * Generischer Knoten des Hierarchiebaums.
 *
 * `actions` und `children` sind absichtlich verpflichtend. Das Backend
 * liefert für fehlende Werte jeweils eine leere Liste. Dadurch müssen
 * Komponenten nicht zwischen `undefined` und einer leeren Liste
 * unterscheiden.
 */
export interface HierarchyNode {
  /**
   * Stabile, innerhalb der Hierarchie eindeutige ID.
   */
  id: HierarchyNodeId;

  /**
   * Fachlicher Knotentyp.
   *
   * Das Frontend rendert ausschließlich bekannte Knotentypen über seine
   * feste Registry. Unbekannte Typen werden sichtbar als nicht unterstützt
   * dargestellt.
   */
  type: HierarchyNodeType;

  /**
   * Anzeigename des Knotens.
   */
  name: string;

  /**
   * Vom Backend grundsätzlich angebotene Aktionen.
   *
   * Eine enthaltene Aktion bedeutet nicht automatisch, dass sie ohne
   * weitere serverseitige Autorisierung ausgeführt werden darf.
   */
  actions: HierarchyActionKind[];

  /**
   * Untergeordnete Knoten.
   */
  children: HierarchyNode[];

  /**
   * ID des übergeordneten Knotens.
   *
   * Beim Wurzelknoten ist dieser Wert normalerweise `null`.
   */
  parent_id?: HierarchyNodeId | null;

  /**
   * Nicht negativer Sortierwert innerhalb desselben Elternknotens.
   */
  sort_order?: number | null;

  /**
   * Gibt an, ob der Knoten durch den Benutzer ausgewählt werden kann.
   *
   * Fehlt der Wert, gilt der Knoten standardmäßig als auswählbar.
   */
  selectable?: boolean | null;

  /**
   * Gibt an, ob der Knoten deaktiviert dargestellt werden soll.
   *
   * Die serverseitige Autorisierung bleibt davon unberührt.
   */
  disabled?: boolean | null;

  /**
   * Optionaler maschinenlesbarer Status.
   */
  status?: string | null;

  /**
   * Freie, vom Backend validierte Zusatzdaten.
   */
  metadata?: HierarchyNodeMetadata | null;

  /**
   * Optionale Revision dieses einzelnen Knotens.
   */
  revision?: number | null;
}

/**
 * Versionierter Hierarchiebaum des Backends.
 */
export interface HierarchyTree {
  /**
   * Version des Hierarchievertrags.
   */
  schema_version: string;

  /**
   * Wurzelknoten.
   */
  root: HierarchyNode;

  /**
   * Globale Revision für Cache-Invalidierung.
   */
  revision?: number | null;
}

/**
 * Prüft einen unbekannten Wert auf die Struktur eines Hierarchieknotens.
 *
 * Dies ist eine reine Laufzeit-Strukturprüfung. Beziehungen wie eindeutige
 * IDs, korrekte `parent_id`-Werte oder Zyklen müssen beim Einlesen des
 * gesamten Baums separat geprüft werden.
 */
export function isHierarchyNode(value: unknown): value is HierarchyNode {
  if (!isRecord(value)) {
    return false;
  }

  const {
    id,
    type,
    name,
    actions,
    children,
    parent_id,
    sort_order,
    selectable,
    disabled,
    status,
    metadata,
    revision,
  } = value;

  return (
    isNonEmptyString(id) &&
    isNonEmptyString(type) &&
    isNonEmptyString(name) &&
    Array.isArray(actions) &&
    actions.every(isNonEmptyString) &&
    Array.isArray(children) &&
    children.every(isHierarchyNode) &&
    isOptionalNullableNonEmptyString(parent_id) &&
    isOptionalNullableNonNegativeInteger(sort_order) &&
    isOptionalNullableBoolean(selectable) &&
    isOptionalNullableBoolean(disabled) &&
    isOptionalNullableNonEmptyString(status) &&
    isOptionalNullableRecord(metadata) &&
    isOptionalNullableNonNegativeInteger(revision)
  );
}

/**
 * Prüft einen unbekannten Wert auf die Struktur eines Hierarchiebaums.
 */
export function isHierarchyTree(value: unknown): value is HierarchyTree {
  if (!isRecord(value)) {
    return false;
  }

  const { schema_version, root, revision } = value;

  return (
    isNonEmptyString(schema_version) &&
    isHierarchyNode(root) &&
    isOptionalNullableNonNegativeInteger(revision)
  );
}

/**
 * Prüft zusätzlich zu `isHierarchyTree`, ob die erwartete
 * Schemaversion verwendet wird.
 */
export function isSupportedHierarchyTree(value: unknown): value is HierarchyTree {
  return isHierarchyTree(value) && value.schema_version === HIERARCHY_SCHEMA_VERSION;
}

/**
 * Prüft, ob ein unbekannter Wert ein Objekt mit String-Schlüsseln ist.
 *
 * Arrays werden absichtlich ausgeschlossen.
 */
export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

export function isOptionalNullableNonEmptyString(
  value: unknown,
): value is string | null | undefined {
  return value === undefined || value === null || isNonEmptyString(value);
}

export function isOptionalNullableBoolean(value: unknown): value is boolean | null | undefined {
  return value === undefined || value === null || typeof value === 'boolean';
}

export function isOptionalNullableInteger(value: unknown): value is number | null | undefined {
  return (
    value === undefined ||
    value === null ||
    (typeof value === 'number' && Number.isFinite(value) && Number.isInteger(value))
  );
}

export function isOptionalNullableNonNegativeInteger(
  value: unknown,
): value is number | null | undefined {
  return (
    value === undefined ||
    value === null ||
    (typeof value === 'number' && Number.isFinite(value) && Number.isInteger(value) && value >= 0)
  );
}

export function isOptionalNullableRecord(
  value: unknown,
): value is Record<string, unknown> | null | undefined {
  return value === undefined || value === null || isRecord(value);
}

/**
 * Typ für den Anlegenvorgang eines neuen Knotens, wie er vom Frontend an das
 * Backend gesendet wird. ID und Kinder werden serverseitig erzeugt.
 */
export type HierarchyNodeCreate = Omit<HierarchyNode, 'id' | 'children' | 'revision'> & {
  parent_id?: HierarchyNodeId | null;
};

/**
 * Typ für Teilupdates an einem Knoten. Alle Felder sind optional, da nur die
 * geänderten Werte übertragen werden.
 */
export type HierarchyNodeUpdate = Partial<
  Pick<
    HierarchyNode,
    | 'name'
    | 'type'
    | 'actions'
    | 'metadata'
    | 'parent_id'
    | 'sort_order'
    | 'selectable'
    | 'disabled'
    | 'status'
  >
>;
