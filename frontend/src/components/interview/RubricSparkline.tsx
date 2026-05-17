"use client";

/**
 * RubricSparkline — Front-upgrade §6.19. Tiny mono trend line, no axes,
 * no tooltip. Renders inline inside a TrendStrip chip.
 */

interface RubricSparklineProps {
  points: number[];
  /** Score range 0..max (default 10) */
  max?: number;
  width?: number;
  height?: number;
  className?: string;
}

export function RubricSparkline({
  points,
  max = 10,
  width = 60,
  height = 24,
  className,
}: RubricSparklineProps) {
  if (points.length < 2) {
    return (
      <span
        aria-hidden
        className={className}
        style={{ display: "inline-block", width, height, opacity: 0.4 }}
      >
        <svg viewBox={`0 0 ${width} ${height}`} width={width} height={height}>
          <line
            x1={2}
            y1={height / 2}
            x2={width - 2}
            y2={height / 2}
            stroke="currentColor"
            strokeWidth={1}
            strokeDasharray="2 3"
          />
        </svg>
      </span>
    );
  }
  const step = (width - 4) / (points.length - 1);
  const path = points
    .map((v, i) => {
      const x = 2 + i * step;
      const y = height - 2 - (Math.max(0, Math.min(max, v)) / max) * (height - 4);
      return `${i === 0 ? "M" : "L"}${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");
  return (
    <span aria-hidden className={className} style={{ display: "inline-block", width, height }}>
      <svg viewBox={`0 0 ${width} ${height}`} width={width} height={height}>
        <path d={path} fill="none" stroke="currentColor" strokeWidth={1.25} strokeLinejoin="round" />
      </svg>
    </span>
  );
}
