"use client";

import Link from "next/link";
import { CalendarDays, ExternalLink, MoreHorizontal } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/badge";
import { formatDeadline } from "@/lib/utils";
import type { SavedOpportunity } from "@/lib/api/types";

interface SavedRowProps {
  saved: SavedOpportunity;
  onPromote: () => void;
  onRemove: () => void;
  promoting?: boolean;
}

export function SavedRow({ saved, onPromote, onRemove, promoting }: SavedRowProps) {
  const s = saved.scholarship;
  const dl = s.deadline ? formatDeadline(s.deadline) : null;
  const [menuOpen, setMenuOpen] = useState(false);
  const savedAt = new Date(saved.saved_at).toLocaleDateString("en-GB", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <li
      data-testid="saved-row"
      className="flex flex-col gap-3 rounded-[18px] border border-[var(--color-border)] bg-paper-white p-5 md:flex-row md:items-center md:justify-between"
    >
      <div className="min-w-0 flex-1">
        <Link
          href={`/scholarships/${s.id}`}
          className="block text-[17px] font-semibold leading-tight text-ink-deep hover:underline underline-offset-4"
        >
          {s.title}
        </Link>
        <p className="mt-1 truncate text-[13px] text-ink-muted">{s.provider}</p>
        <div className="mt-3 flex flex-wrap items-center gap-2 text-[12px] text-ink-muted">
          <span className="inline-flex items-center gap-1 font-mono">
            <CalendarDays className="size-3.5" strokeWidth={1.5} aria-hidden />
            Saved {savedAt}
          </span>
          {dl ? (
            <Chip tone={dl.tone === "urgent" ? "caution" : dl.tone === "passed" ? "sindoor" : "neutral"}>
              {dl.label}
            </Chip>
          ) : null}
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <Button size="sm" variant="secondary" onClick={onPromote} loading={promoting}>
          Move to tracker
        </Button>
        <div className="relative">
          <button
            type="button"
            aria-label="More actions"
            aria-haspopup="menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
            onBlur={() => window.setTimeout(() => setMenuOpen(false), 120)}
            className="inline-flex size-9 items-center justify-center rounded-[10px] text-ink-muted hover:bg-paper-warm hover:text-ink-deep tap-target"
          >
            <MoreHorizontal className="size-4" strokeWidth={1.5} />
          </button>
          {menuOpen ? (
            <div
              role="menu"
              className="absolute right-0 top-full z-10 mt-1 min-w-[180px] rounded-[12px] border border-[var(--color-border)] bg-paper-white p-1 shadow-[var(--shadow-raised)]"
            >
              <Link
                href={`/scholarships/${s.id}`}
                role="menuitem"
                className="flex w-full items-center gap-2 rounded-[8px] px-3 py-2 text-left text-[13px] text-ink-deep hover:bg-paper-warm"
              >
                <ExternalLink className="size-3.5" strokeWidth={1.5} aria-hidden />
                Open detail
              </Link>
              <button
                type="button"
                role="menuitem"
                onClick={onRemove}
                className="flex w-full items-center gap-2 rounded-[8px] px-3 py-2 text-left text-[13px] text-sindoor hover:bg-[var(--color-sindoor-soft)]"
              >
                Remove from saved
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </li>
  );
}
