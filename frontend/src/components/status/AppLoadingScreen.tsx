// src/components/AppLoadingScreen.tsx
import React from 'react';
import { Loader2 } from 'lucide-react'; // oder eine andere Icon-Bibliothek

export function AppLoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900 p-6">
      <div className="w-full max-w-4xl bg-white dark:bg-slate-800 rounded-lg shadow-lg overflow-hidden grid grid-cols-1 md:grid-cols-2">
        {/* Linke Spalte: Branding / Info */}
        <div className="p-8 md:p-12 bg-linear-to-b from-white to-slate-50 dark:from-slate-800 dark:to-slate-900 flex flex-col justify-center">
          <div className="flex items-center gap-4">
            <img src="/favicon.png" alt="Kernschmied" className="h-12 w-12" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Kernschmied</h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
                Zentrale Kommunikations- und Assistenzplattform
              </p>
            </div>
          </div>

          <div className="mt-8 space-y-3 text-sm text-gray-700 dark:text-gray-300">
            <p className="leading-relaxed">
              Chats, Informationen, Projekte und Werkzeuge in einem gemeinsamen,
              sicher kontrollierten Arbeitskontext.
            </p>
            <ul className="space-y-2">
              <li>• Schema‑gesteuerte Oberfläche</li>
              <li>• Dynamische Hierarchie</li>
              <li>• Lokale und externe KI‑Modelle</li>
              <li>• Nachvollziehbare Aktionen</li>
            </ul>
          </div>
        </div>

        {/* Rechte Spalte: Ladeanzeige */}
        <div className="p-8 md:p-12 flex flex-col items-center justify-center">
          <div className="flex flex-col items-center gap-6">
            <Loader2 className="h-16 w-16 text-sky-600 animate-spin" />
            <div className="text-center">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                App wird geladen …
              </h2>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                Bitte warten Sie einen Moment.
              </p>
            </div>
            {/* Optional: Fortschrittsbalken, falls vorhanden */}
            <div className="w-full max-w-xs h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div className="h-full w-2/3 bg-sky-600 rounded-full animate-pulse" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}