// F:\Kernschmied\frontend\src\app\useAppBootstrap.ts

import { useCallback } from 'react';
import { useAppStoreCommands, useAppStoreState } from '../store';
import type { AppBootstrap } from '../types/bootstrap';
import type {
  HierarchyNodeCreate,
  HierarchyNodeUpdate,
  HierarchyTree,
} from '../contracts/hierarchy';
import {
  createHierarchyNode as apiCreateHierarchyNode,
  updateHierarchyNode as apiUpdateHierarchyNode,
  moveHierarchyNode as apiMoveHierarchyNode,
  reorderHierarchy as apiReorderHierarchy,
  deleteHierarchyNode as apiDeleteHierarchyNode,
} from '../api/hierarchy';

interface UseAppBootstrapOptions {
  /** Die Bootstrap‑Daten der App */
  bootstrap?: AppBootstrap | null;
  /** Funktion zum Neuladen der gesamten App (Schema + Hierarchie) */
  reload?: () => Promise<void>;
  /** Funktion zum Neuladen der Hierarchie (nur Baum) */
  reloadHierarchy?: () => Promise<void>;
}

/**
 * useAppBootstrap – zentrale Hook für Hierarchie‑Mutationen und App‑Reload.
 *
 * Stellt Funktionen bereit, um:
 * - Knoten zu erstellen, zu aktualisieren, zu verschieben und zu löschen
 * - Die Hierarchie neu zu laden
 * - Die gesamte App neu zu laden
 * - Knoten auszuwählen und die expandierten Knoten zu verwalten
 *
 * @param options - Konfiguration (Bootstrap, Reload‑Funktionen)
 * @returns Objekt mit allen Funktionen und State
 */
export function useAppBootstrap(options?: UseAppBootstrapOptions) {
  const state = useAppStoreState();
  const { selectHierarchyNode, replaceExpandedNodeIds } = useAppStoreCommands();

  /**
   * Erstellt einen neuen Hierarchie‑Knoten.
   *
   * @param payloadOrParentId - Entweder die ID des Elternknotens (dann wird ein Standard‑Chat erstellt) oder ein vollständiges `HierarchyNodeCreate`‑Objekt.
   * @returns Die erstellte Knoten‑ID (falls verfügbar)
   */
  const createHierarchyNode = useCallback(
    async (payloadOrParentId: string | (HierarchyNodeCreate & Record<string, unknown>)) => {
      let payload: HierarchyNodeCreate;

      if (typeof payloadOrParentId === 'string') {
        // Komfort‑API: mit parentId -> Standard‑Chat erstellen
        payload = {
          type: 'chat',
          name: 'Neuer Knoten',
          parent_id: payloadOrParentId || null,
          tool_policy: {},
          config_overrides: {},
          metadata: {},
        } as unknown as HierarchyNodeCreate;
      } else {
        payload = payloadOrParentId as HierarchyNodeCreate;
      }

      // Knoten erstellen
      const created = await apiCreateHierarchyNode(payload as any);
      const createdId = (created as any)?.id;

      // Hierarchie neu laden (optional)
      try {
        if (options?.reloadHierarchy) {
          await options.reloadHierarchy();
        }
      } catch (reloadError) {
        // Reload‑Fehler werden nicht an den Aufrufer weitergegeben,
        // aber der neu erstellte Knoten könnte trotzdem im Store sein.
        console.warn('[useAppBootstrap] Reload after create failed:', reloadError);
      }

      // Neu erstellten Knoten selektieren (wenn ID vorhanden)
      if (createdId && typeof selectHierarchyNode === 'function') {
        try {
          selectHierarchyNode(createdId);
        } catch (selectionError) {
          console.warn('[useAppBootstrap] Selection of new node failed:', selectionError);
        }
      }

      return createdId;
    },
    [options?.reloadHierarchy, selectHierarchyNode],
  );

  /**
   * Aktualisiert einen bestehenden Hierarchie‑Knoten.
   *
   * @param id - ID des zu aktualisierenden Knotens
   * @param payload - Die zu aktualisierenden Felder (name, type, metadata, etc.)
   */
  const updateHierarchyNode = useCallback(
    async (id: string, payload: unknown) => {
      await apiUpdateHierarchyNode(id, payload as HierarchyNodeUpdate);
      try {
        if (options?.reloadHierarchy) {
          await options.reloadHierarchy();
        }
      } catch (reloadError) {
        console.warn('[useAppBootstrap] Reload after update failed:', reloadError);
      }
    },
    [options?.reloadHierarchy],
  );

  /**
   * Verschiebt einen Knoten innerhalb der Hierarchie.
   *
   * @param id - ID des zu verschiebenden Knotens
   * @param newParentId - ID des neuen Elternknotens (oder null für Wurzel)
   * @param position - Optionale Position im neuen Eltern‑Knoten (Sortierung)
   */
  const moveHierarchyNode = useCallback(
    async (id: string, newParentId: string | null, position?: number | null) => {
      if (position === undefined || position === null) {
        await apiMoveHierarchyNode(id, newParentId);
      } else {
        await apiReorderHierarchy([{ id, new_parent_id: newParentId, new_position: position }]);
      }

      try {
        if (options?.reloadHierarchy) {
          await options.reloadHierarchy();
        }
      } catch (reloadError) {
        console.warn('[useAppBootstrap] Reload after move failed:', reloadError);
      }
    },
    [options?.reloadHierarchy],
  );

  /**
   * Löscht einen Hierarchie‑Knoten.
   *
   * @param id - ID des zu löschenden Knotens
   */
  const deleteHierarchyNode = useCallback(
    async (id: string) => {
      await apiDeleteHierarchyNode(id);
      try {
        if (options?.reloadHierarchy) {
          await options.reloadHierarchy();
        }
      } catch (reloadError) {
        console.warn('[useAppBootstrap] Reload after delete failed:', reloadError);
      }
    },
    [options?.reloadHierarchy],
  );

  /**
   * Löst ein vollständiges Neuladen der App aus (Schema + Hierarchie).
   */
  const reloadApplication = useCallback((): void => {
    if (options?.reload) {
      void options.reload();
    }
  }, [options?.reload]);

  return {
    /** Die Bootstrap‑Daten (oder null) */
    bootstrap: options?.bootstrap ?? null,
    /** Der aktuelle App‑Store‑State */
    state,
    /** Löst ein vollständiges Neuladen der App aus */
    reloadApplication,
    /** Wählt einen Knoten in der Hierarchie aus (Store‑Action) */
    selectHierarchyNode,
    /** Ersetzt die Menge der expandierten Knoten‑IDs (Store‑Action) */
    replaceExpandedNodeIds,
    /** Erstellt einen neuen Hierarchie‑Knoten */
    createHierarchyNode,
    /** Aktualisiert einen bestehenden Hierarchie‑Knoten */
    updateHierarchyNode,
    /** Verschiebt einen Knoten */
    moveHierarchyNode,
    /** Löscht einen Knoten */
    deleteHierarchyNode,
  };
}