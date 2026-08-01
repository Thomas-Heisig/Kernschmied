import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { HierarchyNode } from '../../contracts/hierarchy';
import { Modal } from './Modal';

type ActionKind = 'create_chat' | 'rename' | 'move' | 'delete' | 'edit_prompt';

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
    // Initialize the input value when the modal opens or when the
    // acted-on node changes (use id for stability). Avoid depending on
    // the full `node` object which may be recreated on every render
    // and would reset the input while the user types.
    if (!isOpen) return;

    if (kind === 'edit_prompt') {
      const existing = (node as any)?.metadata?.prompt ?? '';
      setValue(typeof existing === 'string' ? existing : '');
      return;
    }

    if (kind === 'rename') {
      setValue(node?.name ?? '');
      return;
    }

    // create_chat and move start with empty input
    setValue('');
  }, [isOpen, kind, node?.id]);

  useEffect(() => {
    if (!isOpen) return;
    // Focus the input or textarea inside the modal if present. This runs
    // after Modal's own focus to ensure typing works immediately.
    const t = window.setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
    return () => window.clearTimeout(t);
  }, [isOpen, kind]);

  const title = useMemo(() => {
    switch (kind) {
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
        <div className="text-sm">
          Soll <strong>{node?.name}</strong> wirklich gelöscht werden?
        </div>
      ) : null}

      {(kind === 'rename' || kind === 'create_chat' || kind === 'move') && (
        <div className="mt-2" onMouseDown={(e) => e.stopPropagation()}>
          <label className="block text-sm text-text-muted">
            {kind === 'move' ? 'ID des neuen Elternknotens (leer = Root)' : 'Name'}
          </label>
          <input
            className="mt-1 w-full rounded border border-border px-2 py-1"
            value={value}
            ref={inputRef as any}
            onChange={(e) => {
              // debug: ensure change events fire

              console.debug('HierarchyActionModal input onChange', e.target.value);
              setValue(e.target.value);
            }}
            onFocus={() => {
              console.debug('HierarchyActionModal input onFocus');
            }}
          />
        </div>
      )}

      {kind === 'edit_prompt' && (
        <div className="mt-2" onMouseDown={(e) => e.stopPropagation()}>
          <label className="block text-sm text-text-muted">System-/Kontext-Prompt</label>
          <textarea
            className="mt-1 w-full rounded border border-border px-2 py-1"
            rows={6}
            value={value}
            ref={inputRef as any}
            onChange={(e) => {
              console.debug('HierarchyActionModal textarea onChange', e.target.value);
              setValue(e.target.value);
            }}
            onFocus={() => {
              console.debug('HierarchyActionModal textarea onFocus');
            }}
          />
        </div>
      )}

      {loading ? <div className="mt-3 text-sm text-text-muted">Bitte warten…</div> : null}
    </Modal>
  );
}

export default HierarchyActionModal;
