"use client";

/**
 * CompatibilityMeter — neutral 0..1 → percent bar used on match rows.
 * Reads the design-system tokens defined in `src/app/globals.css`.
 */

type Props = { value: number };

export function CompatibilityMeter({ value }: Props) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div
      className="flex items-center gap-2"
      aria-label={`Compatibility ${pct}%`}
    >
      <div className="h-1.5 w-24 rounded-full bg-ink/10">
        <div
          className="h-full rounded-full bg-ink transition-[width] duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-ink-muted tabular-nums">{pct}%</span>
    </div>
  );
}
