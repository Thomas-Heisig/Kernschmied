// F:\Kernschmied\frontend\src\components\ui\ToastProvider.tsx

import React, { createContext, useCallback, useContext, useState } from 'react';
import { CheckCircle, AlertCircle, Info, XCircle, X } from 'lucide-react';
import IconBadge from '../common/IconBadge';

type ToastKind = 'info' | 'success' | 'error';

interface ToastItem {
  id: string;
  kind: ToastKind;
  message: string;
}

interface ToastContextValue {
  push: (kind: ToastKind, message: string, ttl?: number) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}

const TOAST_ICONS: Record<ToastKind, React.ReactNode> = {
  success: <CheckCircle />,
  error: <XCircle />,
  info: <Info />,
};

const TOAST_VARIANTS: Record<ToastKind, { variant: 'success' | 'danger' | 'default'; bg: string }> = {
  success: { variant: 'success', bg: 'bg-success-soft dark:bg-success/10' },
  error: { variant: 'danger', bg: 'bg-danger-soft dark:bg-danger/10' },
  info: { variant: 'default', bg: 'bg-primary-soft dark:bg-primary/10' },
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const push = useCallback((kind: ToastKind, message: string, ttl = 4000) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setToasts((prev) => [...prev, { id, kind, message }]);

    if (ttl > 0) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, ttl);
    }
  }, []);

  const remove = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div className="fixed right-4 top-4 z-50 flex max-w-sm w-full flex-col gap-2 pointer-events-none">
        {toasts.map((toast) => {
          const { variant, bg } = TOAST_VARIANTS[toast.kind];
          const icon = TOAST_ICONS[toast.kind];
          return (
            <div
              key={toast.id}
              className={[
                'pointer-events-auto flex items-start gap-3 rounded-xl border border-border-soft bg-white/95 p-4 shadow-2xl backdrop-blur-sm animate-slide-in dark:border-white/10 dark:bg-slate-900/95',
                bg,
              ].join(' ')}
              role="status"
              aria-live="polite"
            >
              <div className="shrink-0">
                <IconBadge icon={icon} size="md" variant={variant} />
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm text-text-soft dark:text-gray-300">{toast.message}</p>
              </div>

              <button
                type="button"
                className="shrink-0 rounded-lg p-1 text-text-muted transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
                onClick={() => remove(toast.id)}
                aria-label="Benachrichtigung schließen"
              >
                <IconBadge icon={<X />} size="sm" variant="default" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export default ToastProvider;