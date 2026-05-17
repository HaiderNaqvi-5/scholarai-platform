/**
 * Premium Cultural design tokens — mirror of globals.css `@theme` block.
 * Use these in TypeScript when you need a token value at runtime (e.g.,
 * recharts palettes, dynamic style objects). For CSS, prefer the
 * `var(--color-…)` references directly.
 *
 * Source: Front-upgrade.md §2 (Design Foundations).
 */
export const themeTokens = {
  colors: {
    /* Paper */
    ivory: "#FBF7EE",
    paperWarm: "#F3ECDC",
    paperEdge: "#E5DAC2",
    paperWhite: "#FFFDF9",
    /* Ink */
    inkDeep: "#0E1A1F",
    ink: "#1B2630",
    inkMuted: "#4A5663",
    inkSubtle: "#6E7984",
    /* Accents */
    lapis: "#1B3A6B",
    lapisSoft: "#DCE3EE",
    goldLeaf: "#B08A3E",
    goldSoft: "#F1E6CA",
    sindoor: "#B94A48",
    sindoorSoft: "#F2D9D5",
    /* Semantic */
    validated: "#426B5A",
    validatedSoft: "#DDE9E2",
    generated: "#2E5B9A",
    generatedSoft: "#DCE6F4",
    caution: "#B7791F",
    cautionSoft: "#F4E7CF",
  },
  surfaces: {
    page: "var(--color-ivory)",
    panel: "var(--color-paper-white)",
    muted: "var(--color-paper-warm)",
    raised: "var(--color-paper-white)",
  },
  spacing: [4, 8, 12, 16, 20, 24, 32, 48, 64, 96] as const,
  radii: {
    input: "10px",
    sm: "10px",
    button: "12px",
    card: "18px",
    panel: "22px",
    hero: "28px",
    pill: "999px",
  },
  elevation: {
    hairline: "inset 0 0 0 1px rgba(14,26,31,0.10)",
    lift: "0 1px 2px rgba(14,26,31,0.04), 0 8px 24px -12px rgba(14,26,31,0.10)",
    raised: "0 12px 32px -16px rgba(14,26,31,0.18)",
  },
  motion: {
    micro: "90ms",
    enter: "180ms",
    exit: "140ms",
    layout: "220ms",
    easeOut: "cubic-bezier(0.22, 1, 0.36, 1)",
    easeIn: "cubic-bezier(0.32, 0, 0.67, 0)",
  },
  text: {
    display: "var(--font-display), ui-serif, Georgia, serif",
    ui: "var(--font-ui), ui-sans-serif, system-ui, sans-serif",
    mono: "var(--font-mono), ui-monospace, monospace",
  },
} as const;

/** Recharts palette — neutral, never rainbow (Front-upgrade §2.5). */
export const chartPalette = [
  themeTokens.colors.lapis,
  themeTokens.colors.goldLeaf,
  themeTokens.colors.validated,
  themeTokens.colors.sindoor,
  themeTokens.colors.inkMuted,
] as const;
