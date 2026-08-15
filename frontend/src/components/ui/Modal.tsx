// F:\Kernschmied\frontend\src\components\ui\Modal.tsx

import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import IconBadge from '../common/IconBadge';

export interface ModalProps {
  isOpen: boolean;
  title?: string | null;
  children: React.ReactNode;
  onClose: () => void;
  onConfirm?: () => void;
  confirmLabel?: string;
  confirmDisabled?: boolean;
  /** 'primary' (Standard) oder 'danger' (für Lösch‑Aktionen) */
  confirmVariant?: 'primary' | 'danger';
}

export function Modal({
  isOpen,
  title,
  children,
  onClose,
  onConfirm,
  confirmLabel = 'OK',
  confirmDisabled = false,
  confirmVariant = 'primary',
}: ModalProps) {
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    closeButtonRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const confirmButtonClass =
    confirmVariant === 'danger'
      ? 'bg-danger text-white hover:bg-danger-hover focus-visible:ring-danger dark:bg-danger/80 dark:hover:bg-danger'
      : 'bg-primary text-white shadow-glow hover:bg-primary-hover hover:shadow-primary-glow focus-visible:ring-primary dark:bg-primary/80 dark:hover:bg-primary';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <section
        className="w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-2xl border border-border-soft bg-white shadow-2xl dark:border-white/10 dark:bg-slate-900"
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'modal-title' : undefined}
        onMouseDown={(e) => e.stopPropagation()}
      >
        {/* Kopfzeile */}
        <header className="flex items-center justify-between gap-3 border-b border-border-soft px-5 py-3.5 dark:border-white/10">
          <h2
            id="modal-title"
            className="text-base font-semibold text-text dark:text-white"
          >
            {title}
          </h2>
          <button
            ref={closeButtonRef}
            type="button"
            className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-text-muted transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
            onClick={onClose}
            aria-label="Schließen"
          >
            <IconBadge icon={<X />} size="sm" variant="default" />
          </button>
        </header>

        {/* Inhalt */}
        <div className="px-5 py-4">{children}</div>

        {/* Footer (optional – nur bei onConfirm) */}
        {onConfirm && (
          <footer className="flex flex-wrap items-center justify-end gap-3 border-t border-border-soft px-5 py-3.5 dark:border-white/10">
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-lg border border-border-soft px-4 py-2 text-sm font-medium text-text-soft transition hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:border-white/10 dark:text-gray-300 dark:hover:bg-slate-800"
              onClick={onClose}
            >
              Abbrechen
            </button>
            <button
              type="button"
              className={[
                'inline-flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-medium text-white shadow-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                confirmButtonClass,
              ].join(' ')}
              onClick={onConfirm}
              disabled={confirmDisabled}
            >
              {confirmLabel}
            </button>
          </footer>
        )}
      </section>
    </div>
  );
}

export default Modal;