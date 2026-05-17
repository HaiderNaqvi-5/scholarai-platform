"use client";

import { RubricSparkline } from "./RubricSparkline";

interface Trend {
  dimension: string;
  points: number[];
  /** Most recent value, used for the leading number */
  latest: number | null;
}

interface TrendStripProps {
  trends: Record<string, { points: { at: string; score: number }[] }>;
  /** Cap how many dimensions render */
  max?: number;
}

const TITLE_FOR: Record<string, string> = {
  motivation: "Motivation",
  finances: "Finances",
  ties: "Ties",
  communication: "Communication",
  overall: "Overall",
  clarity: "Clarity",
  specificity: "Specificity",
  evidence: "Evidence",
  confidence: "Confidence",
  cadence: "Cadence",
};

function prettyDimension(d: string): string {
  const key = d.toLowerCase();
  if (TITLE_FOR[key]) return TITLE_FOR[key];
  return d.charAt(0).toUpperCase() + d.slice(1);
}

/**
 * TrendStrip — Front-upgrade §6.19. Horizontal scrollable strip of 5
 * rubric chips. Each chip: dimension name + latest score (mono) +
 * mini sparkline of trend.
 */
export function TrendStrip({ trends, max = 5 }: TrendStripProps) {
  const entries: Trend[] = Object.entries(trends)
    .slice(0, max)
    .map(([dimension, data]) => ({
      dimension,
      points: data.points.map((p) => p.score),
      latest: data.points.length > 0 ? data.points[data.points.length - 1].score : null,
    }));

  if (entries.length === 0) return null;

  return (
    <div className="flex w-full gap-3 overflow-x-auto py-1" aria-label="Rubric trends">
      {entries.map((e) => (
        <div
          key={e.dimension}
          className="flex min-w-[160px] shrink-0 items-center gap-3 rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 py-2"
        >
          <div className="min-w-0 flex-1">
            <p className="font-mono text-[10px] uppercase tracking-[0.06em] text-ink-subtle">
              {prettyDimension(e.dimension)}
            </p>
            <p className="mt-0.5 font-mono text-[14px] tabular-nums text-ink-deep">
              {e.latest != null ? e.latest.toFixed(1) : "—"}
            </p>
          </div>
          <RubricSparkline points={e.points} className="text-lapis" />
        </div>
      ))}
    </div>
  );
}
