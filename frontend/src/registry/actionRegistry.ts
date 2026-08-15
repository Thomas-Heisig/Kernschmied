// F:\Kernschmied\frontend\src\registry\actionRegistry.ts

import { KNOWN_ACTION_KINDS, type KnownActionKind } from '../contracts/schema';

/**
 * Eine Aktion wird nur dann als unterstützt behandelt, wenn sie:
 *
 * 1. im stabilen Frontend-Vertrag bekannt ist und
 * 2. explizit in dieser Registry eingetragen wurde.
 *
 * Ein vom Backend gelieferter Aktionsname registriert oder aktiviert
 * niemals automatisch neue Frontend-Funktionalität.
 */

export interface ActionContext<TNode = unknown, TPayload = unknown> {
  /**
   * Der Knoten oder Datensatz, auf den sich die Aktion bezieht.
   */
  target?: TNode;

  /**
   * Optionaler, bereits validierter Aktions-Payload.
   */
  payload?: TPayload;

  /**
   * AbortSignal für abbrechbare Aktionen.
   */
  signal?: AbortSignal;
}

export interface ActionResult<TResult = unknown> {
  /**
   * Gibt an, ob die Aktion erfolgreich abgeschlossen wurde.
   */
  success: boolean;

  /**
   * Optionales Ergebnis der Aktion.
   */
  data?: TResult;

  /**
   * Optionaler maschinenlesbarer Ergebnis- oder Fehlercode.
   */
  code?: string;

  /**
   * Optionale Meldung für die Benutzeroberfläche.
   */
  message?: string;
}

export type ActionHandler<TNode = unknown, TPayload = unknown, TResult = unknown> = (
  context: ActionContext<TNode, TPayload>,
) => Promise<ActionResult<TResult>> | ActionResult<TResult>;

export interface ActionDefinition {
  /**
   * Stabiler Aktionsname aus dem versionierten Frontend-Vertrag.
   */
  kind: KnownActionKind;

  /**
   * Benutzerfreundliche Standardbeschriftung.
   */
  label: string;

  /**
   * Optionaler Iconname aus der festen Icon-Registry.
   */
  icon?: string;

  /**
   * Kennzeichnet eine potenziell destruktive Aktion.
   */
  destructive?: boolean;

  /**
   * Verlangt vor der Ausführung eine ausdrückliche Bestätigung.
   */
  confirmationRequired?: boolean;

  /**
   * Gibt an, ob die Aktion derzeit im Frontend sichtbar angeboten
   * werden darf.
   *
   * Dies ersetzt keine serverseitige Autorisierung.
   */
  enabled?: boolean;

  /**
   * Optional registrierter Handler.
   *
   * Aktionen ohne Handler können dargestellt, aber nicht ausgeführt werden.
   */
  handler?: ActionHandler;
}

export type ActionRegistry = ReadonlyMap<KnownActionKind, Readonly<ActionDefinition>>;

/**
 * Hilfsfunktion für noch nicht implementierte Aktionen.
 * Diese Aktionen werden deaktiviert, damit sie im UI nicht angezeigt werden.
 */
function unsupportedAction(label: string, icon?: string): Omit<ActionDefinition, 'kind'> {
  return {
    label,
    icon,
    enabled: false,
  };
}

const actionDefinitions = [
  // ============================================================
  // Bestehende Aktionen (bereits implementiert oder unterstützt)
  // ============================================================
  {
    kind: 'create_child',
    label: 'Unterelement erstellen',
    icon: 'Plus',
    enabled: true,
  },
  {
    kind: 'rename',
    label: 'Umbenennen',
    icon: 'Pencil',
    enabled: true,
  },
  {
    kind: 'delete',
    label: 'Löschen',
    icon: 'Trash2',
    destructive: true,
    confirmationRequired: true,
    enabled: true,
  },
  {
    kind: 'move',
    label: 'Verschieben',
    icon: 'Move',
    enabled: true,
  },
  {
    kind: 'open_form',
    label: 'Formular öffnen',
    icon: 'PanelTopOpen',
    enabled: true,
  },
  {
    kind: 'edit_node',
    label: 'Knoten bearbeiten…',
    icon: 'FilePenLine',
    enabled: true,
  },
  {
    kind: 'edit_config',
    label: 'Knoten konfigurieren…',
    icon: 'SlidersHorizontal',
    enabled: true,
  },
  {
    kind: 'navigate',
    label: 'Öffnen',
    icon: 'ArrowRight',
    enabled: true,
  },
  {
    kind: 'download',
    label: 'Herunterladen',
    icon: 'Download',
    enabled: true,
  },
  {
    kind: 'export',
    label: 'Exportieren',
    icon: 'FileOutput',
    enabled: true,
  },
  {
    kind: 'edit_prompt',
    label: 'Prompt bearbeiten',
    icon: 'FilePenLine',
    enabled: true,
  },
  {
    kind: 'toggle_tools',
    label: 'Werkzeuge umschalten',
    icon: 'Wrench',
    enabled: true,
  },
  {
    kind: 'invoke_operation',
    label: 'Aktion ausführen',
    icon: 'Play',
    enabled: true,
  },
  {
    kind: 'create_chat',
    label: 'Neuer Chat',
    icon: 'MessageSquarePlus',
    enabled: true,
  },

  // ============================================================
  // Noch nicht implementierte Aktionen (deaktiviert)
  // ============================================================
  {
    kind: 'rename_chat',
    ...unsupportedAction('Chat umbenennen', 'Pencil'),
  },
  {
    kind: 'delete_chat',
    ...unsupportedAction('Chat löschen', 'Trash2'),
  },
  {
    kind: 'archive_chat',
    label: 'Archiv umschalten',
    icon: 'Archive',
    enabled: true,
    handler: async (context) => {
      try {
        const target: any = context.target as any;
        if (!target || !target.id) {
          return { success: false, code: 'invalid_target', message: 'Kein gültiges Ziel angegeben.' };
        }

        const { updateHierarchyNode } = await import('../api/hierarchy');

        const currentlyArchived = Boolean(target.metadata?.archived === true);
        const metadata = { ...(target.metadata ?? {}), archived: !currentlyArchived };

        await updateHierarchyNode(target.id, { metadata } as any);

        return { success: true, data: { archived: !currentlyArchived } };
      } catch (err: unknown) {
        return { success: false, message: err instanceof Error ? err.message : 'Fehler beim Umschalten des Archivs' };
      }
    },
  },
  {
    kind: 'export_chat',
    ...unsupportedAction('Chat exportieren', 'FileOutput'),
  },
  {
    kind: 'create_workspace',
    ...unsupportedAction('Workspace erstellen', 'Plus'),
  },
  {
    kind: 'rename_workspace',
    ...unsupportedAction('Workspace umbenennen', 'Pencil'),
  },
  {
    kind: 'delete_workspace',
    ...unsupportedAction('Workspace löschen', 'Trash2'),
  },
  {
    kind: 'create_project',
    ...unsupportedAction('Projekt erstellen', 'Plus'),
  },
  {
    kind: 'rename_project',
    ...unsupportedAction('Projekt umbenennen', 'Pencil'),
  },
  {
    kind: 'delete_project',
    ...unsupportedAction('Projekt löschen', 'Trash2'),
  },
  {
    kind: 'refresh',
    ...unsupportedAction('Aktualisieren', 'RefreshCw'),
  },
  {
    kind: 'settings',
    ...unsupportedAction('Einstellungen', 'Settings'),
  },
  {
    kind: 'help',
    ...unsupportedAction('Hilfe', 'HelpCircle'),
  },
  {
    kind: 'logout',
    ...unsupportedAction('Abmelden', 'LogOut'),
  },
] satisfies readonly ActionDefinition[];

function createActionRegistry(definitions: readonly ActionDefinition[]): ActionRegistry {
  const registry = new Map<KnownActionKind, Readonly<ActionDefinition>>();

  for (const definition of definitions) {
    if (registry.has(definition.kind)) {
      throw new Error(`Die Aktion "${definition.kind}" wurde mehrfach registriert.`);
    }

    registry.set(
      definition.kind,
      Object.freeze({
        ...definition,
      }),
    );
  }

  assertRegistryCompleteness(registry);

  return registry;
}

function assertRegistryCompleteness(
  registry: ReadonlyMap<KnownActionKind, Readonly<ActionDefinition>>,
): void {
  const missingActions = KNOWN_ACTION_KINDS.filter((kind) => !registry.has(kind));

  if (missingActions.length > 0) {
    throw new Error(
      `Für folgende bekannte Aktionen fehlt ein Registry-Eintrag: ${missingActions.join(', ')}`,
    );
  }
}

export const actionRegistry: ActionRegistry = createActionRegistry(actionDefinitions);

/**
 * Prüft ausschließlich, ob ein Wert Bestandteil des stabilen
 * Frontend-Vertrags ist.
 *
 * Diese Prüfung sagt nicht aus, ob ein Handler vorhanden ist oder ob
 * der aktuelle Benutzer die Aktion ausführen darf.
 */
export function isKnownActionKind(value: unknown): value is KnownActionKind {
  return typeof value === 'string' && actionRegistry.has(value as KnownActionKind);
}

/**
 * Gibt die Registry-Definition einer bekannten Aktion zurück.
 */
export function getActionDefinition(kind: string): Readonly<ActionDefinition> | undefined {
  if (!isKnownActionKind(kind)) {
    return undefined;
  }

  return actionRegistry.get(kind);
}

/**
 * Prüft, ob eine bekannte Aktion im Frontend aktiviert ist.
 *
 * Die tatsächliche Berechtigung muss weiterhin serverseitig geprüft werden.
 */
export function isActionEnabled(kind: string): kind is KnownActionKind {
  const definition = getActionDefinition(kind);

  return definition?.enabled !== false;
}

/**
 * Prüft, ob für die Aktion ein ausführbarer Frontend-Handler vorhanden ist.
 */
export function hasActionHandler(kind: string): kind is KnownActionKind {
  const definition = getActionDefinition(kind);

  return typeof definition?.handler === 'function';
}

/**
 * Liefert nur Aktionen zurück, die:
 *
 * - dem Frontend bekannt sind,
 * - in der Registry registriert sind und
 * - nicht explizit deaktiviert wurden.
 *
 * Unbekannte Backend-Aktionen werden sicher verworfen.
 */
export function filterSupportedActionKinds(values: readonly string[]): KnownActionKind[] {
  return values.filter(isActionEnabled);
}

/**
 * Führt eine lokal registrierte Aktion aus.
 *
 * Diese Funktion ist nicht für direkte Backend-Mutationen gedacht.
 * Serverseitige Aktionen sollten über einen zentralen API-Dienst laufen,
 * der Authentifizierung, Autorisierung, Fehlerbehandlung und Auditierung
 * übernimmt.
 */
export async function executeRegisteredAction<
  TNode = unknown,
  TPayload = unknown,
  TResult = unknown,
>(kind: string, context: ActionContext<TNode, TPayload>): Promise<ActionResult<TResult>> {
  const definition = getActionDefinition(kind);

  if (!definition) {
    return {
      success: false,
      code: 'unsupported_action',
      message: `Die Aktion "${kind}" wird vom Frontend nicht unterstützt.`,
    };
  }

  if (definition.enabled === false) {
    return {
      success: false,
      code: 'action_disabled',
      message: `Die Aktion "${kind}" ist derzeit deaktiviert.`,
    };
  }

  if (!definition.handler) {
    return {
      success: false,
      code: 'action_handler_missing',
      message: `Für die Aktion "${kind}" ist kein Frontend-Handler registriert.`,
    };
  }

  if (context.signal?.aborted) {
    return {
      success: false,
      code: 'action_aborted',
      message: 'Die Aktion wurde abgebrochen.',
    };
  }

  try {
    return (await definition.handler(context)) as ActionResult<TResult>;
  } catch (error) {
    return {
      success: false,
      code: 'action_execution_failed',
      message:
        error instanceof Error ? error.message : 'Die Aktion konnte nicht ausgeführt werden.',
    };
  }
}

/**
 * Alle registrierten Aktionsdefinitionen als unveränderliche Liste.
 *
 * Geeignet für Menüs, Toolbars oder Diagnoseansichten.
 */
export function listActionDefinitions(): readonly Readonly<ActionDefinition>[] {
  return Array.from(actionRegistry.values());
}
