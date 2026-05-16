"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type Tone = "neutral" | "validated" | "caution" | "danger" | "generated" | "ink";

/**
 * Generic Kanban column: header (label + count badge) + drop target with
 * native HTML5 DnD. Shared by /tracker and /saved so the over-state ring,
 * empty-column placeholder, and badge tones stay consistent.
 */
export function KanbanColumn({
  label,
  count,
  tone = "neutral",
  isOver,
  onDragOver,
  onDragLeave,
  onDrop,
  children,
  emptyLabel = "Empty",
}: {
  label: string;
  count: number;
  tone?: Tone;
  isOver: boolean;
  onDragOver: (e: React.DragEvent<HTMLDivElement>) => void;
  onDragLeave: () => void;
  onDrop: () => void;
  children: React.ReactNode;
  emptyLabel?: string;
}) {
  return (
    <div
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      className={cn(
        "rounded-[16px] border border-[var(--color-border)] bg-paper-warm/40 p-3 transition-colors duration-150",
        isOver && "ring-2 ring-[var(--color-ring)] bg-paper-warm",
      )}
    >
      <div className="mb-3 flex items-center justify-between gap-2 px-1">
        <h2 className="font-display text-sm uppercase tracking-wider text-ink-muted">
          {label}
        </h2>
        <Badge tone={tone}>{count}</Badge>
      </div>
      <div className="space-y-3">
        {count === 0 ? (
          <p className="px-2 py-4 text-center text-xs text-ink-subtle">{emptyLabel}</p>
        ) : (
          children
        )}
      </div>
    </div>
  );
}
