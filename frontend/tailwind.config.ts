import type { Config } from "tailwindcss";

export default {
  // Dark Mode über Klasse (manueller Schalter)
  darkMode: "class",

  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],

  theme: {
    extend: {
      // ─── Farben ──────────────────────────────────────────────────────
      colors: {
        primary: {
          DEFAULT: "#2563eb",
          hover: "#1d4ed8",
          active: "#1e40af",
          soft: "rgba(37, 99, 235, 0.1)",
          medium: "rgba(37, 99, 235, 0.18)",
          glow: "rgba(37, 99, 235, 0.28)",
        },
        secondary: {
          DEFAULT: "#7c3aed",
          soft: "rgba(124, 58, 237, 0.12)",
        },
        accent: {
          DEFAULT: "#0891b2",
          soft: "rgba(8, 145, 178, 0.12)",
        },
        success: {
          DEFAULT: "#16a34a",
          soft: "rgba(22, 163, 74, 0.12)",
        },
        warning: {
          DEFAULT: "#d97706",
          soft: "rgba(217, 119, 6, 0.12)",
        },
        danger: {
          DEFAULT: "#dc2626",
          soft: "rgba(220, 38, 38, 0.12)",
        },
        info: {
          DEFAULT: "#0284c7",
          soft: "rgba(2, 132, 199, 0.12)",
        },
        text: {
          DEFAULT: "#0f172a",
          soft: "#334155",
          muted: "#64748b",
          subtle: "#94a3b8",
          inverse: "#ffffff",
        },
        surface: {
          DEFAULT: "rgba(255, 255, 255, 0.82)",
          solid: "#ffffff",
          muted: "rgba(248, 250, 252, 0.9)",
          hover: "rgba(255, 255, 255, 0.96)",
          active: "#eff6ff",
        },
        border: {
          DEFAULT: "rgba(148, 163, 184, 0.26)",
          soft: "rgba(148, 163, 184, 0.16)",
          strong: "rgba(100, 116, 139, 0.36)",
        },
      },

      // ─── Radien (weicher) ──────────────────────────────────────────
      borderRadius: {
        xs: "0.375rem",
        sm: "0.5rem",
        md: "0.75rem",
        lg: "1rem",
        xl: "1.5rem", // bisher 1.25rem → weicher
        "2xl": "2rem", // bisher 1.75rem → weicher
        "3xl": "2.5rem", // neu für besonders weiche Elemente
      },

      // ─── Schatten (mit Glas-Effekt) ──────────────────────────────
      boxShadow: {
        xs: "0 1px 2px rgba(15, 23, 42, 0.04)",
        sm: "0 1px 3px rgba(15, 23, 42, 0.05), 0 4px 12px rgba(15, 23, 42, 0.04)",
        md: "0 4px 10px rgba(15, 23, 42, 0.06), 0 14px 32px rgba(15, 23, 42, 0.07)",
        lg: "0 8px 24px rgba(15, 23, 42, 0.08), 0 28px 70px rgba(15, 23, 42, 0.1)",
        xl: "0 18px 50px rgba(15, 23, 42, 0.14), 0 4px 14px rgba(15, 23, 42, 0.08)",
        // Neue Glasschatten
        glass: "0 8px 32px rgba(0, 0, 0, 0.08), 0 2px 8px rgba(0, 0, 0, 0.04)",
        "glass-lg":
          "0 16px 48px rgba(0, 0, 0, 0.12), 0 4px 16px rgba(0, 0, 0, 0.06)",
        // Bestehende spezielle Schatten
        glow: "0 10px 30px rgba(37, 99, 235, 0.25)",
        "primary-glow": "0 0 12px rgba(37, 99, 235, 0.28)",
      },

      // ─── Animationen ──────────────────────────────────────────────
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(7px) scale(0.995)" },
          to: { opacity: "1", transform: "translateY(0) scale(1)" },
        },
        "slide-in-left": {
          from: { opacity: "0", transform: "translateX(-10px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        pulse: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.55" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.24s ease-out both",
        "slide-in": "slide-in-left 0.22s ease-out both",
        shimmer: "shimmer 1.6s infinite",
        pulse: "pulse 2s ease-in-out infinite",
      },

      // ─── Layout ──────────────────────────────────────────────────
      spacing: {
        header: "4rem",
        sidebar: "18rem",
      },

      // ─── Übergänge ──────────────────────────────────────────────
      transitionDuration: {
        fast: "120ms",
        DEFAULT: "180ms",
        slow: "280ms",
      },
      transitionTimingFunction: {
        DEFAULT: "ease",
      },
    },
  },

  plugins: [],
} satisfies Config;
