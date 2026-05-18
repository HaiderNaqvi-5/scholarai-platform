"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

const WORDS = ["bachelor's", "master's", "PhD"] as const;
const HOLD_MS = 2200;
const FADE_MS = 320;

/**
 * Cycles "bachelor's → master's → PhD" in the hero headline. Opacity-only
 * transition (no layout animation per §2.4), pauses for prefers-reduced-motion,
 * uses `aria-live="polite"` so screen readers announce each change once.
 */
export function RotatingDegree({ className }: { className?: string }) {
  const [index, setIndex] = useState(0);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const reduced =
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;

    if (reduced) {
      const tick = window.setInterval(() => {
        setIndex((n) => (n + 1) % WORDS.length);
      }, HOLD_MS + FADE_MS);
      return () => window.clearInterval(tick);
    }

    const tick = window.setInterval(() => {
      setVisible(false);
      window.setTimeout(() => {
        setIndex((n) => (n + 1) % WORDS.length);
        setVisible(true);
      }, FADE_MS);
    }, HOLD_MS + FADE_MS);

    return () => window.clearInterval(tick);
  }, []);

  return (
    <span
      aria-live="polite"
      aria-atomic="true"
      className={cn(
        "inline-block min-w-[5ch] transition-opacity ease-out",
        visible ? "opacity-100" : "opacity-0",
        className,
      )}
      style={{ transitionDuration: `${FADE_MS}ms` }}
    >
      {WORDS[index]}
    </span>
  );
}
