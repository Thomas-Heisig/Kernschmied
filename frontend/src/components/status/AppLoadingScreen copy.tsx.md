// F:\Kernschmied\frontend\src\components\status\AppLoadingScreen.tsx

import React, { useEffect, useState, useRef } from 'react';

// Normale Ladesprüche
const loadingQuotes = [
  '⚒️ Schärfe die Klingen …',
  '🔥 Heize den Kern vor …',
  '🔨 Klopf, klopf – wer da? Der Amboss!',
  '🌀 Wir schmieden eine gute Verbindung …',
  '⚙️ Zahnräder werden geölt …',
  '💡 Ideen werden geschmiedet …',
  '🛠️ Werkzeuge werden sortiert …',
  '🌟 Ein bisschen Magie für den Kern …',
  '⚡ Blitze des Fortschritts …',
  '📡 Verbindung zum Amboss wird aufgebaut …',
  '🧙‍♂️ Ein Meister schmiedet im Hintergrund …',
  '🎯 Ziel erfasst: Deine Anfrage …',
  '🍃 Ein Hauch von Kohlenstaub …',
  '🎵 Schmiede-Ballade läuft …',
  '🤖 KI wird geschmiedet …',
  '🛡️ Schutzschild wird gehärtet …',
  '🏰 Der Kernschmied rüstet auf …',
  '🌀 Portal wird geöffnet …',
  '☕ Kaffee für den Schmied wird gebrüht …',
];

// Pausen-Sprüche – wenn der Schmied eine Pause macht
const pauseQuotes = [
  '😴 Kurze Pause – der Schmied trinkt Kaffee …',
  '🛋️ Amboss ruht sich aus …',
  '☕ Kaffeepause – gleich geht’s weiter …',
  '💤 Der Kern schläft noch …',
  '🧘 Meister meditiert …',
  '🎯 Ziele werden neu ausgerichtet …',
  '📖 Rezept wird gelesen …',
  '🎶 Ohrenbetäubende Stille …',
  '🕰️ Zeit für einen Moment der Einkehr …',
  '🌿 Der Schmied atmet tief durch …',
];

// Hammer-Emojis für die Animation
const hammerEmojis = ['🔨', '⚒️', '🛠️', '🔧', '⛏️'];

interface AppLoadingScreenProps {
  onReady?: () => void;
}

export function AppLoadingScreen({ onReady }: AppLoadingScreenProps) {
  const [quoteIndex, setQuoteIndex] = useState(0);
  const [hammerIndex, setHammerIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [pauseQuoteIndex, setPauseQuoteIndex] = useState(0);

  // Timer mit korrektem Typ für Browser-Umgebungen
  const pauseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const quoteTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hammerTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Informiere Aufrufer nach etwa 5 Sekunden, dass die Ladeanzeige fertig ist
  useEffect(() => {
    const timer = setTimeout(() => {
      onReady?.();
    }, 5000);
    return () => clearTimeout(timer);
  }, [onReady]);

  // Zyklus: 8 Sekunden arbeiten, dann 2,5 Sekunden Pause
  useEffect(() => {
    const cycle = () => {
      setIsPaused(false);
      // Nach 8 Sekunden Pause einlegen
      pauseTimerRef.current = setTimeout(() => {
        setIsPaused(true);
        setPauseQuoteIndex(Math.floor(Math.random() * pauseQuotes.length));
        // Nach 2,5 Sekunden wieder arbeiten
        const resumeTimer = setTimeout(() => {
          setIsPaused(false);
          // Neustart des Zyklus
          cycle();
        }, 2500);
        // Speichere den Resume-Timer nicht im Ref, da er innerhalb der Callback-Funktion liegt
        // und automatisch cleanup durchgeführt wird, wenn die Komponente unmountet.
        // Wir speichern ihn aber im Ref, um ihn bei unmount zu clearen.
        pauseTimerRef.current = resumeTimer;
      }, 8000);
    };
    cycle();

    return () => {
      if (pauseTimerRef.current) clearTimeout(pauseTimerRef.current);
    };
  }, []);

  // Spruchwechsel – in der Pause werden Pausen-Sprüche angezeigt
  useEffect(() => {
    // Alten Timer löschen
    if (quoteTimerRef.current) clearInterval(quoteTimerRef.current);

    if (isPaused) {
      // Während der Pause wechseln wir die Pausen-Sprüche alle 1,2 Sekunden
      quoteTimerRef.current = setInterval(() => {
        setPauseQuoteIndex((prev) => (prev + 1) % pauseQuotes.length);
      }, 1200);
    } else {
      // Normale Ladesprüche alle 1,8 Sekunden
      quoteTimerRef.current = setInterval(() => {
        setQuoteIndex((prev) => (prev + 1) % loadingQuotes.length);
      }, 1800);
    }
    return () => {
      if (quoteTimerRef.current) clearInterval(quoteTimerRef.current);
    };
  }, [isPaused]);

  // Hammer-Animation – in der Pause friert der Hammer ein (oder wird langsamer)
  useEffect(() => {
    if (hammerTimerRef.current) clearInterval(hammerTimerRef.current);

    if (isPaused) {
      // In der Pause wechselt der Hammer nur alle 2 Sekunden (träge)
      hammerTimerRef.current = setInterval(() => {
        setHammerIndex((prev) => (prev + 1) % hammerEmojis.length);
      }, 2000);
    } else {
      // Normal: alle 400 ms
      hammerTimerRef.current = setInterval(() => {
        setHammerIndex((prev) => (prev + 1) % hammerEmojis.length);
      }, 400);
    }
    return () => {
      if (hammerTimerRef.current) clearInterval(hammerTimerRef.current);
    };
  }, [isPaused]);

  // Fortschrittsbalken – in der Pause pausiert der Fortschritt
  useEffect(() => {
    let startTime = performance.now();
    let rafId: number;

    const updateProgress = (now: number) => {
      if (isPaused) {
        // In der Pause bleibt der Fortschritt stehen
        rafId = requestAnimationFrame(updateProgress);
        return;
      }
      const elapsed = (now - startTime) / 1000;
      // Sinusförmiger Fortschritt zwischen 0 und 100, Periode ~ 6 Sekunden
      const value = 50 + 50 * Math.sin(elapsed * 0.4);
      setProgress(Math.round(value));
      rafId = requestAnimationFrame(updateProgress);
    };

    rafId = requestAnimationFrame(updateProgress);
    return () => cancelAnimationFrame(rafId);
  }, [isPaused]);

  return (
    <main
      className="flex h-full min-h-0 items-center justify-center bg-linear-to-br from-amber-50/80 to-orange-100/80 p-6 dark:from-slate-900/60 dark:to-slate-800/60"
      aria-busy="true"
      aria-live="polite"
      aria-label="Anwendung wird geladen"
    >
      <section className="animate-fade-in relative max-w-md w-full rounded-3xl border border-amber-200/50 bg-white/90 px-8 py-10 shadow-2xl backdrop-blur-md transition-all dark:border-amber-800/30 dark:bg-slate-800/90">
        {/* Schmiede-Elemente – dekorativ */}
        <div className="absolute -top-3 -left-3 text-4xl opacity-30 select-none rotate-12">
          ⚒️
        </div>
        <div className="absolute -bottom-3 -right-3 text-4xl opacity-30 select-none -rotate-12">
          🔥
        </div>

        <div className="flex flex-col items-center gap-5">
          {/* Kopf: Logo + Hammer-Animation */}
          <div className="flex items-center gap-4">
            <span className="text-6xl transition-all duration-300">
              {hammerEmojis[hammerIndex]}
            </span>
            <span className="text-5xl font-black tracking-tight text-amber-800 dark:text-amber-300">
              Kern<span className="text-amber-600 dark:text-amber-400">schmied</span>
            </span>
          </div>

          {/* Fortschrittsbalken – mit Pausen-Anzeige */}
          <div className="w-full max-w-xs">
            <div className="relative h-3 w-full overflow-hidden rounded-full bg-amber-200/60 dark:bg-amber-800/40 shadow-inner">
              <div
                className={`h-full rounded-full bg-linear-to-r from-amber-500 via-orange-500 to-amber-600 transition-all duration-300 ${
                  isPaused ? 'ease-in' : 'ease-out'
                }`}
                style={{ width: `${progress}%` }}
                role="progressbar"
                aria-valuenow={progress}
                aria-valuemin={0}
                aria-valuemax={100}
              />
              {/* Funken – in der Pause verschwinden sie */}
              {!isPaused && (
                <div
                  className="absolute top-0 h-full w-2 bg-white/40 blur-sm animate-pulse"
                  style={{ left: `${Math.min(progress + 5, 95)}%` }}
                />
              )}
            </div>
            <div className="mt-1 flex justify-between text-xs text-amber-700/70 dark:text-amber-300/60">
              <span>{isPaused ? '⏸️ Pause' : 'Amboss kalt'}</span>
              <span>{progress}% geschmiedet</span>
              <span>{isPaused ? '☕ Ruhe' : 'Glühend heiß'}</span>
            </div>
          </div>

          {/* Der aktuelle Ladespruch – mit Pausen-Hinweis */}
          <div className="min-h-14 flex items-center justify-center">
            <p className="text-center text-lg font-medium text-amber-800 dark:text-amber-200 transition-all duration-300">
              {isPaused ? pauseQuotes[pauseQuoteIndex] : loadingQuotes[quoteIndex]}
            </p>
          </div>

          {/* Kleiner Hinweis – zeigt den aktuellen Zustand an */}
          <div className="text-xs text-amber-600/60 dark:text-amber-400/40 flex items-center gap-1">
            <span>{isPaused ? '💤' : '🔨'}</span>
            <span>
              {isPaused
                ? 'Der Schmied macht eine kurze Pause'
                : 'Der Schmied arbeitet mit Hochdruck'}
            </span>
            <span>{isPaused ? '🛋️' : '⚒️'}</span>
          </div>

          {/* Footer-Spruch – je nach Zustand variiert */}
          <div className="mt-2 text-[10px] text-amber-500/40 dark:text-amber-400/30 italic select-none">
            {isPaused
              ? '„Auch der beste Schmied braucht eine Rast.“'
              : '„Jeder gute Kern braucht Zeit zum Schmieden.“'}
          </div>
        </div>
      </section>
    </main>
  );
}