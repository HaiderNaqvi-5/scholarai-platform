"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface Option {
  value: string;
  label: string;
}

interface MultiChipProps {
  options: Option[];
  selected: string[];
  onToggle: (value: string) => void;
  ariaLabel?: string;
}

/**
 * MultiChip — multi-select chip group. Tap to toggle; rendered as
 * `<button role="checkbox" aria-checked>` for screen-reader correctness.
 * Premium Cultural: lapis-soft selected fill, hairline neutral resting.
 */
export function MultiChip({ options, selected, onToggle, ariaLabel }: MultiChipProps) {
  return (
    <div role="group" aria-label={ariaLabel} className="flex flex-wrap gap-2">
      {options.map((o) => {
        const active = selected.includes(o.value);
        return (
          <button
            key={o.value}
            type="button"
            role="checkbox"
            aria-checked={active}
            onClick={() => onToggle(o.value)}
            className={cn(
              "inline-flex h-9 items-center gap-1.5 rounded-[10px] border px-3 text-[13px] transition-colors duration-[var(--motion-micro)] ease-[var(--ease-out)] tap-target",
              active
                ? "border-lapis bg-lapis-soft text-lapis"
                : "border-[var(--color-border)] bg-paper-white text-ink-muted hover:bg-paper-warm hover:text-ink-deep",
            )}
          >
            {active ? <Check className="size-3.5" strokeWidth={2} aria-hidden /> : null}
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
