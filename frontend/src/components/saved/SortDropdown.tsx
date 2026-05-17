"use client";

import type { ChangeEvent } from "react";

export type SavedSort = "recent" | "deadline";

interface SortDropdownProps {
  value: SavedSort;
  onChange: (next: SavedSort) => void;
}

export function SortDropdown({ value, onChange }: SortDropdownProps) {
  const handle = (e: ChangeEvent<HTMLSelectElement>) => onChange(e.target.value as SavedSort);
  return (
    <label className="inline-flex items-center gap-2 text-[13px] text-ink-muted">
      Sort by
      <select
        value={value}
        onChange={handle}
        className="h-9 rounded-[10px] border border-[var(--color-border)] bg-paper-white px-3 text-[13px] text-ink-deep focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
      >
        <option value="recent">Recently saved</option>
        <option value="deadline">Deadline</option>
      </select>
    </label>
  );
}
