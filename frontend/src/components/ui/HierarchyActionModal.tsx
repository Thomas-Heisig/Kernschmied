// F:\Kernschmied\frontend\src\components\ui\HierarchyActionModal.tsx

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { HierarchyNode } from '../../contracts/hierarchy';
import { Modal } from './Modal';

type ActionKind = 'create_child' | 'create_chat' | 'rename' | 'move' | 'delete' | 'edit_prompt';

export function HierarchyActionModal({
  isOpen,
  kind,
  node,
  onClose,
  onConfirm,
  loading = false,
}: {
  isOpen: boolean;
  kind?: ActionKind | null;
  node?: HierarchyNode | null;
  onClose: () => void;
  onConfirm: (value?: string | null) => void;
  loading?: boolean;
}) {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    if (kind === 'edit_prompt') {
      const existing = (node as any)?.system_prompt ?? (node as any)?.metadata?.prompt ?? '';
      setValue(typeof existing === 'string' ? existing : '');
      return;
    }

    if (kind === 'rename') {
      setValue(node?.name ?? '');
      return;
    }

    setValue('');
  }, [isOpen, kind, node?.id]);

  useEffect(() => {
    if (!isOpen) return;
    const t = window.setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
    return () => window.clearTimeout(t);
  }, [isOpen, kind]);

  const title = useMemo(() => {
    switch (kind) {
      case 'create_child':
        return `Neues Unterelement in ${node?.name ?? '...'} erstellen`;
      case 'create_chat':
        return `Neuen Chat in ${node?.name ?? '...'} erstellen`;
      case 'rename':
        return `Umbenennen: ${node?.name ?? '...'}`;
      case 'move':
        return `Verschieben: ${node?.name ?? '...'}`;
      case 'delete':
        return `Löschen: ${node?.name ?? '...'}`;
      case 'edit_prompt':
        return `Prompt bearbeiten: ${node?.name ?? '...'}`;
      default:
        return 'Aktion';
    }
  }, [kind, node]);

  const confirmLabel = useMemo(() => {
    switch (kind) {
      case 'create_child':
        return 'Erstellen';
      case 'create_chat':
        return 'Erstellen';
      case 'rename':
        return 'Umbenennen';
      case 'move':
        return 'Verschieben';
      case 'delete':
        return 'Löschen';
      case 'edit_prompt':
        return 'Speichern';
      default:
        return 'OK';
    }
  }, [kind]);

  const onConfirmClick = useCallback(() => {
    onConfirm(value || null);
  }, [onConfirm, value]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (import.meta.env.DEV) {
      console.debug('HierarchyActionModal input onChange', e.target.value);
    }
    setValue(e.target.value);
  }, []);

  return (
    <Modal
      isOpen={isOpen}
      title={title}
      onClose={onClose}
      onConfirm={onConfirmClick}
      confirmLabel={confirmLabel}
      confirmDisabled={loading}
    >
      {kind === 'delete' ? (
        <div className="text-sm text-text-soft dark:text-gray-300">
          Soll <strong className="text-text dark:text-white">{node?.name}</strong> wirklich gelöscht werden?
        </div>
      ) : null}

      {(kind === 'rename' || kind === 'create_child' || kind === 'create_chat' || kind === 'move') && (
        <div className="mt-3" onMouseDown={(e) => e.stopPropagation()}>
          <label
            htmlFor="hierarchy-action-input"
            className="block text-sm font-medium text-text-soft dark:text-gray-300"
          >
            {kind === 'move' ? 'ID des neuen Elternknotens (leer = Root)' : 'Name'}
          </label>
          <input
            id="hierarchy-action-input"
            className="mt-1.5 w-full rounded-lg border border-border-soft bg-surface-muted px-3 py-2 text-sm text-text outline-none transition placeholder:text-text-subtle focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-60 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:placeholder:text-gray-500 dark:focus:ring-primary/20"
            value={value}
            ref={inputRef as any}
            onChange={handleChange}
            onFocus={() => {
              if (import.meta.env.DEV) console.debug('HierarchyActionModal input onFocus');
            }}
            placeholder={kind === 'move' ? 'Eltern-ID eingeben…' : 'Name eingeben…'}
          />
        </div>
      )}

      {kind === 'edit_prompt' && (
        <div className="mt-3" onMouseDown={(e) => e.stopPropagation()}>
          <label
            htmlFor="hierarchy-action-textarea"
            className="block text-sm font-medium text-text-soft dark:text-gray-300"
          >
            System‑/Kontext‑Prompt
          </label>
          <textarea
            id="hierarchy-action-textarea"
            className="mt-1.5 w-full rounded-lg border border-border-soft bg-surface-muted px-3 py-2 text-sm text-text outline-none transition placeholder:text-text-subtle focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-60 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:placeholder:text-gray-500 dark:focus:ring-primary/20"
            rows={6}
            value={value}
            ref={inputRef as any}
            onChange={handleChange}
            onFocus={() => {
              if (import.meta.env.DEV) console.debug('HierarchyActionModal textarea onFocus');
            }}
            placeholder="Prompt eingeben…"
          />
        </div>
      )}

      {loading && (
        <div className="mt-3 text-sm text-text-muted dark:text-gray-400">
          Bitte warten…
        </div>
      )}
    </Modal>
  );
}

export default HierarchyActionModal;