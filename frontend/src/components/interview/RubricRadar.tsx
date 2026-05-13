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

export function RubricRadar({ dimensions }: { dimensions: InterviewRubricDimension[] }) {
  if (dimensions.length === 0) {
    return (
      <p className="py-10 text-center text-sm text-ink-subtle">
        Answer a question to see rubric scores.
      </p>
    );
  }
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
            domain={[0, 5]}
            tick={{ fill: "var(--color-ink-subtle)", fontSize: 10 }}
            tickCount={6}
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
