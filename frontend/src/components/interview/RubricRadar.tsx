"use client";

import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";
import type { InterviewRubricDimension } from "@/lib/api";

type Scale = "0-5" | "0-10";

/**
 * Radar over rubric dimensions. Pass `scale` so the caller doesn't have to
 * pre-divide visa-interview 0-10 scores before passing them in — the chart
 * handles axis range + label formatting from one switch.
 */
export function RubricRadar({
  dimensions,
  scale = "0-5",
}: {
  dimensions: InterviewRubricDimension[];
  scale?: Scale;
}) {
  if (dimensions.length === 0) {
    return (
      <p className="py-10 text-center text-sm text-ink-subtle">
        Answer a question to see rubric scores.
      </p>
    );
  }
  const max = scale === "0-10" ? 10 : 5;
  const data = dimensions.map((d) => ({ dimension: d.dimension, score: d.score }));
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} outerRadius="70%">
          <PolarGrid stroke="var(--color-border)" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fill: "var(--color-ink-muted)", fontSize: 12 }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, max]}
            tick={{ fill: "var(--color-ink-subtle)", fontSize: 10 }}
            tickCount={max === 10 ? 6 : 6}
          />
          <Radar
            dataKey="score"
            stroke="var(--color-validated)"
            fill="var(--color-validated)"
            fillOpacity={0.3}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
