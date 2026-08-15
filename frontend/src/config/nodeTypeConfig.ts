// F:\Kernschmied\frontend\src\config\nodeTypeConfig.ts

export interface NodeTypeConfig {
  /** Icon‑Name aus dem DynamicIcon‑Registry */
  icon: string;
  /** Visuelle Variante für IconBadge */
  variant: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  /** Standardgröße für IconBadge (kann im Context überschrieben werden) */
  defaultSize: 'sm' | 'md' | 'lg';
  /** Anzeigename (optional) */
  label?: string;
  /** Hintergrundfarbe (optional, überschreibt variant) */
  color?: string | null;
  /** Erlaubte Kindtypen (für Struktur‑Validierung) */
  allowedChildTypes: string[];
  /** Erlaubte Aktionen (für Workspace‑Aktionsleiste) */
  allowedActions: string[];
  /** Knoten‑Flags (für UI‑Verhalten) */
  selectable: boolean;
  draggable: boolean;
  droppable: boolean;
  expandable: boolean;
  /** Sichtbarkeit (public/authenticated/private) */
  visibility: string;
  /** Erforderliche Berechtigungen */
  requiredPermissions: string[];
  /** Zusätzliche Metadaten */
  metadata: Record<string, unknown>;
}

/**
 * Factory für Projekt‑Konfigurationen (vermeidet Duplikate).
 */
function createProjectConfig(overrides?: Partial<NodeTypeConfig>): NodeTypeConfig {
  return {
    icon: 'Folder',
    variant: 'primary',
    defaultSize: 'md',
    label: 'Projekt',
    color: '#3b82f6',
    allowedChildTypes: ['chat', 'conversation', 'website', 'webseite'],
    allowedActions: ['rename', 'delete', 'create_child', 'edit_prompt', 'toggle_tools'],
    selectable: true,
    draggable: false,
    droppable: false,
    expandable: true,
    visibility: 'authenticated',
    requiredPermissions: [],
    metadata: {},
    ...overrides,
  };
}

/**
 * Zentrale Konfiguration für alle Hierarchie‑Knotentypen.
 *
 * Definiert Icon, Farbe, Größe und Verhalten für jeden Knotentyp.
 * Wird in Sidebars, Tree, Workspace‑Headern und Widgets verwendet.
 */
export const NODE_TYPE_CONFIG: Record<string, NodeTypeConfig> = {
  // ============================================================
  // SYSTEM
  // ============================================================
  system: {
    icon: 'LayoutDashboard',
    variant: 'primary',
    defaultSize: 'md',
    label: 'System',
    allowedChildTypes: ['user', 'benutzer'],
    allowedActions: ['rename', 'edit_prompt', 'toggle_tools'],
    selectable: true,
    expandable: true,
    draggable: false,
    droppable: false,
    visibility: 'authenticated',
    requiredPermissions: ['system:read'],
    metadata: {},
  },

  // ============================================================
  // BENUTZER (deutsch & englisch)
  // ============================================================
  benutzer: {
    icon: 'User',
    variant: 'secondary',
    defaultSize: 'md',
    label: 'Benutzer',
    allowedChildTypes: ['workspace', 'bereich'],
    allowedActions: ['rename', 'delete', 'create_child', 'edit_prompt'],
    selectable: true,
    expandable: true,
    draggable: false,
    droppable: false,
    visibility: 'authenticated',
    requiredPermissions: ['user:read'],
    metadata: {},
  },
  user: {
    icon: 'User',
    variant: 'secondary',
    defaultSize: 'md',
    label: 'Benutzer',
    allowedChildTypes: ['workspace', 'bereich'],
    allowedActions: ['rename', 'delete', 'create_child', 'edit_prompt'],
    selectable: true,
    expandable: true,
    draggable: false,
    droppable: false,
    visibility: 'authenticated',
    requiredPermissions: ['user:read'],
    metadata: {},
  },

  // ============================================================
  // BEREICH / WORKSPACE
  // ============================================================
  bereich: {
    icon: 'Building2',
    variant: 'success',
    defaultSize: 'md',
    label: 'Bereich',
    allowedChildTypes: ['project', 'projekt', 'website', 'webseite', 'chat', 'conversation'],
    allowedActions: ['rename', 'delete', 'create_child', 'edit_prompt', 'toggle_tools'],
    selectable: true,
    expandable: true,
    draggable: false,
    droppable: false,
    visibility: 'authenticated',
    requiredPermissions: ['workspace:read'],
    metadata: {},
  },
  workspace: {
    icon: 'Building2',
    variant: 'success',
    defaultSize: 'md',
    label: 'Bereich',
    allowedChildTypes: ['project', 'projekt', 'website', 'webseite', 'chat', 'conversation'],
    allowedActions: ['rename', 'delete', 'create_child', 'edit_prompt', 'toggle_tools'],
    selectable: true,
    expandable: true,
    draggable: false,
    droppable: false,
    visibility: 'authenticated',
    requiredPermissions: ['workspace:read'],
    metadata: {},
  },

  // ============================================================
  // PROJEKT (deutsch & englisch)
  // ============================================================
  projekt: createProjectConfig({ label: 'Projekt' }),
  project: createProjectConfig({ label: 'Projekt' }),

  // ============================================================
  // CHAT (deutsch & englisch)
  // ============================================================
  chat: {
    icon: 'MessageSquare',
    variant: 'default',
    defaultSize: 'md',
    label: 'Chat',
    allowedChildTypes: [],
    allowedActions: ['rename', 'delete', 'edit_prompt'],
    selectable: true,
    expandable: false,
    draggable: false,
    droppable: false,
    visibility: 'authenticated',
    requiredPermissions: ['chat:read'],
    metadata: {},
  },
  conversation: {
    icon: 'MessageSquare',
    variant: 'default',
    defaultSize: 'md',
    label: 'Chat',
    allowedChildTypes: [],
    allowedActions: ['rename', 'delete', 'edit_prompt'],
    selectable: true,
    expandable: false,
    draggable: false,
    droppable: false,
    visibility: 'authenticated',
    requiredPermissions: ['chat:read'],
    metadata: {},
  },

  // ============================================================
  // WEBSEITE (deutsch & englisch)
  // ============================================================
  website: {
    icon: 'Globe2',
    variant: 'default',
    defaultSize: 'md',
    label: 'Webseite',
    allowedChildTypes: [],
    allowedActions: ['rename', 'delete', 'edit_prompt'],
    selectable: true,
    expandable: false,
    draggable: false,
    droppable: false,
    visibility: 'authenticated',
    requiredPermissions: ['website:read'],
    metadata: {},
  },
  webseite: {
    icon: 'Globe2',
    variant: 'default',
    defaultSize: 'md',
    label: 'Webseite',
    allowedChildTypes: [],
    allowedActions: ['rename', 'delete', 'edit_prompt'],
    selectable: true,
    expandable: false,
    draggable: false,
    droppable: false,
    visibility: 'authenticated',
    requiredPermissions: ['website:read'],
    metadata: {},
  },

  // ============================================================
  // EINSTELLUNGEN / KONFIGURATION (Aliase)
  // ============================================================
  'system-configuration': {
    icon: 'Settings',
    variant: 'primary',
    defaultSize: 'md',
    label: 'Systemkonfiguration',
    allowedChildTypes: [],
    allowedActions: ['edit_prompt', 'toggle_tools'],
    selectable: true,
    expandable: false,
    draggable: false,
    droppable: false,
    visibility: 'authenticated',
    requiredPermissions: ['config:read'],
    metadata: {},
  },
  settings: {
    icon: 'Settings',
    variant: 'primary',
    defaultSize: 'md',
    label: 'Einstellungen',
    allowedChildTypes: [],
    allowedActions: ['edit_prompt', 'toggle_tools'],
    selectable: true,
    expandable: false,
    draggable: false,
    droppable: false,
    visibility: 'authenticated',
    requiredPermissions: ['config:read'],
    metadata: {},
  },
  configuration: {
    icon: 'Settings',
    variant: 'primary',
    defaultSize: 'md',
    label: 'Konfiguration',
    allowedChildTypes: [],
    allowedActions: ['edit_prompt', 'toggle_tools'],
    selectable: true,
    expandable: false,
    draggable: false,
    droppable: false,
    visibility: 'authenticated',
    requiredPermissions: ['config:read'],
    metadata: {},
  },
};

/**
 * Holt die Konfiguration für einen Knotentyp (mit Fallback).
 *
 * @param type - Der Knotentyp (z. B. 'project', 'user', 'system')
 * @returns NodeTypeConfig – immer gültig (Fallback für unbekannte Typen)
 */
export function getNodeTypeConfig(type: string): NodeTypeConfig {
  const key = (type ?? '').trim().toLowerCase();
  const config = NODE_TYPE_CONFIG[key];

  if (config) {
    return config;
  }

  // Fallback für unbekannte Typen
  return {
    icon: 'Box',
    variant: 'default',
    defaultSize: 'md',
    label: key || 'node',
    allowedChildTypes: [],
    allowedActions: [],
    selectable: true,
    expandable: false,
    draggable: false,
    droppable: false,
    visibility: 'authenticated',
    requiredPermissions: [],
    metadata: {},
  };
}

/**
 * Hilfsfunktion: Prüft, ob ein Knotentyp in der Konfiguration existiert.
 */
export function hasNodeTypeConfig(type: string): boolean {
  const key = (type ?? '').trim().toLowerCase();
  return key in NODE_TYPE_CONFIG;
}

/**
 * Hilfsfunktion: Holt alle definierten Knotentypen (für Debug‑/Admin‑Views).
 */
export function getAllNodeTypes(): string[] {
  return Object.keys(NODE_TYPE_CONFIG);
}