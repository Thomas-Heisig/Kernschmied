import React, { useEffect, useRef } from 'react';

export function Modal({
  isOpen,
  title,
  children,
  onClose,
  onConfirm,
  confirmLabel = 'OK',
  confirmDisabled = false,
}: {
  isOpen: boolean;
  title?: string | null;
  children: React.ReactNode;
  onClose: () => void;
  onConfirm?: () => void;
  confirmLabel?: string;
  confirmDisabled?: boolean;
}) {
  const ref = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    ref.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener('keydown', onKey);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 flex items-center justify-center bg-slate-950/55 p-3 backdrop-blur-sm"
      style={{ zIndex: 99999 }}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <section
        className="w-full max-w-xl rounded-xl border border-border bg-white shadow-2xl dark:border-white/10 dark:bg-slate-950"
        role="dialog"
        aria-modal="true"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between gap-2 border-b border-border px-4 py-3">
          <h2 className="text-sm font-semibold">{title}</h2>
          <button
            ref={ref}
            type="button"
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg"
            onClick={onClose}
            aria-label="Schließen"
          >
            ✕
          </button>
        </header>

        <div className="px-4 py-4">{children}</div>

        <footer className="flex gap-2 justify-end border-t border-border px-4 py-3">
          <button type="button" className="rounded px-3 py-2 text-sm" onClick={onClose}>
            Abbrechen
          </button>
          <button
            type="button"
            className="rounded bg-primary px-3 py-2 text-sm text-white"
            onClick={onConfirm}
            disabled={confirmDisabled}
          >
            {confirmLabel}
          </button>
        </footer>
      </section>
    </div>
  );
}

export default Modal;
