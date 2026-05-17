"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onChange: (next: number) => void;
}

function pageWindow(current: number, totalPages: number): (number | "…")[] {
  if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i + 1);
  const out: (number | "…")[] = [1];
  const start = Math.max(2, current - 1);
  const end = Math.min(totalPages - 1, current + 1);
  if (start > 2) out.push("…");
  for (let i = start; i <= end; i++) out.push(i);
  if (end < totalPages - 1) out.push("…");
  out.push(totalPages);
  return out;
}

/**
 * Pagination — Front-upgrade §4.2. prev / numbered / next.
 * Disabled state when only one page. Ellipsis for ≥5 pages.
 */
export function Pagination({ page, pageSize, total, onChange }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (totalPages <= 1) return null;
  const cells = pageWindow(page, totalPages);
  const cell =
    "inline-flex h-9 w-9 items-center justify-center rounded-[10px] border border-[var(--color-border)] bg-paper-white text-[13px] text-ink-deep hover:bg-paper-warm disabled:opacity-50 disabled:hover:bg-paper-white";
  return (
    <nav aria-label="Pagination" className="mt-6 flex flex-wrap items-center justify-center gap-1">
      <button
        type="button"
        className={cell}
        onClick={() => onChange(Math.max(1, page - 1))}
        disabled={page <= 1}
        aria-label="Previous page"
      >
        <ChevronLeft className="size-4" strokeWidth={1.5} aria-hidden />
      </button>
      {cells.map((c, i) =>
        c === "…" ? (
          <span
            key={`g-${i}`}
            aria-hidden
            className="inline-flex h-9 w-9 items-center justify-center text-[13px] text-ink-subtle"
          >
            …
          </span>
        ) : (
          <button
            key={c}
            type="button"
            onClick={() => onChange(c)}
            aria-current={c === page ? "page" : undefined}
            className={
              c === page
                ? "inline-flex h-9 w-9 items-center justify-center rounded-[10px] bg-ink-deep text-[13px] font-medium text-paper-white"
                : cell
            }
          >
            {c}
          </button>
        ),
      )}
      <button
        type="button"
        className={cell}
        onClick={() => onChange(Math.min(totalPages, page + 1))}
        disabled={page >= totalPages}
        aria-label="Next page"
      >
        <ChevronRight className="size-4" strokeWidth={1.5} aria-hidden />
      </button>
    </nav>
  );
}
