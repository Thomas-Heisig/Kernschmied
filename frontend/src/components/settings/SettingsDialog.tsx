// F:\Kernschmied\frontend\src\components\settings\SettingsDialog.tsx

import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";

import { useSystemConfig } from "../../hooks/useSystemConfig";
import { SettingsSidebar } from "./SettingsSidebar";
import { SettingsContent } from "./SettingsContent";

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsDialog({ isOpen, onClose }: SettingsDialogProps) {
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);
  const config = useSystemConfig();

  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [showJson, setShowJson] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setActiveKey(null);
      setShowJson(false);
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    closeButtonRef.current?.focus();

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  function handleBackdropMouseDown(event: React.MouseEvent<HTMLDivElement>) {
    if (event.target !== event.currentTarget) return;
    onClose();
  }

  return (
    <div
      className={[
        "fixed inset-0 z-50 flex items-center justify-center",
        "bg-slate-950/50 p-3 backdrop-blur-sm",
        "sm:p-5 lg:p-8",
      ].join(" ")}
      role="presentation"
      onMouseDown={handleBackdropMouseDown}
    >
      <section
        className={[
          "flex min-h-0 w-full max-w-6xl flex-col overflow-hidden rounded-2xl",
          "border border-border-soft bg-white shadow-2xl",
          "dark:border-white/10 dark:bg-slate-950",
          "h-[min(90vh,900px)]",
        ].join(" ")}
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-dialog-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        {/* Dialog-Header – Schriftgewicht reduziert */}
        <header className="flex h-14 shrink-0 items-center justify-between gap-4 border-b border-border bg-white px-4 dark:border-white/10 dark:bg-slate-950 sm:px-5">
          <div className="min-w-0">
            <h1
              id="settings-dialog-title"
              className="truncate text-base font-medium text-text dark:text-white"
            >
              Systemeinstellungen
            </h1>
            <p className="truncate text-xs text-text-muted dark:text-gray-400">
              Fachliche und technische Konfiguration
            </p>
          </div>

          <button
            ref={closeButtonRef}
            type="button"
            className={[
              "inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
              "text-text-soft transition-colors hover:bg-surface-hover hover:text-text",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2",
              "dark:text-gray-300 dark:hover:bg-slate-800 dark:hover:text-white dark:focus-visible:ring-offset-slate-950",
            ].join(" ")}
            aria-label="Einstellungen schließen"
            title="Schließen"
            onClick={onClose}
          >
            <X size={19} aria-hidden="true" />
          </button>
        </header>

        <div className="flex min-h-0 flex-1 overflow-hidden">
          <SettingsSidebar
            values={config.values}
            activeKey={activeKey}
            isJsonActive={showJson}
            onSelectKey={(key) => {
              setActiveKey(key);
              setShowJson(false);
            }}
            onSelectJson={() => {
              setShowJson(true);
              setActiveKey(null);
            }}
          />

          <div className="min-w-0 flex-1 overflow-y-auto">
            <SettingsContent
              activeKey={activeKey}
              showJson={showJson}
              config={config}
            />
          </div>
        </div>
      </section>
    </div>
  );
}
