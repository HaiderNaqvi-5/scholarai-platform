"use client";

import Link from "next/link";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  CalendarRange,
  ChevronLeft,
  ChevronRight,
  Globe,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { endpoints } from "@/lib/api";
import type { ScholarshipListItem } from "@/lib/api";

const CARD_WIDTH = 280;
const CARD_GAP = 16;
const STEP = CARD_WIDTH + CARD_GAP;
const ADVANCE_MS = 5000;
const USER_SCROLL_GRACE_MS = 4000;

const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";

function subscribeReducedMotion(cb: () => void) {
  if (typeof window === "undefined" || !window.matchMedia) return () => {};
  const mm = window.matchMedia(REDUCED_MOTION_QUERY);
  mm.addEventListener("change", cb);
  return () => mm.removeEventListener("change", cb);
}
function getReducedMotion() {
  return (
    typeof window !== "undefined" &&
    !!window.matchMedia &&
    window.matchMedia(REDUCED_MOTION_QUERY).matches
  );
}
function getReducedMotionServer() {
  return false;
}

function formatDeadline(iso: string | null): string {
  if (!iso) return "Rolling deadline";
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

function RailCard({ s }: { s: ScholarshipListItem }) {
  return (
    <li
      className="content-fade-in flex w-[280px] shrink-0 flex-col justify-between rounded-[20px] border border-[var(--color-border)] bg-paper-white p-5 transition-shadow duration-150 hover:shadow-[0_4px_20px_-8px_oklch(0.14_0.04_218/0.12)]"
      style={{ scrollSnapAlign: "start" }}
    >
      <div>
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-display text-[18px] italic font-[450] leading-tight text-ink-deep">
            {s.title}
          </h3>
          <Badge tone="validated" className="shrink-0">
            Live
          </Badge>
        </div>
        {s.provider_name ? (
          <p className="mt-1 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
            {s.provider_name}
          </p>
        ) : null}
      </div>
      <div className="mt-5 flex flex-col gap-1.5">
        <div className="flex items-center gap-2 font-mono text-[11px] text-ink-subtle">
          <CalendarRange className="size-3.5" strokeWidth={1.5} aria-hidden />
          <span>{formatDeadline(s.deadline_at)}</span>
        </div>
        {s.country_code ? (
          <div className="flex items-center gap-2 font-mono text-[11px] text-ink-subtle">
            <Globe className="size-3.5" strokeWidth={1.5} aria-hidden />
            <span>{s.country_code}</span>
          </div>
        ) : null}
      </div>
    </li>
  );
}

function RailSkeleton() {
  return (
    <>
      {Array.from({ length: 6 }).map((_, i) => (
        <li key={i} className="w-[280px] shrink-0" style={{ scrollSnapAlign: "start" }}>
          <Skeleton className="h-[180px] w-full rounded-[20px]" />
        </li>
      ))}
    </>
  );
}

export function ScholarshipsRail() {
  const q = useQuery({
    queryKey: ["scholarships", "rail"],
    queryFn: () => endpoints.scholarships.listPublic({ page_size: 24, sort: "recent" }),
    staleTime: 5 * 60 * 1000,
  });
  const items = q.data?.items ?? [];

  const listRef = useRef<HTMLUListElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const lastUserScrollAt = useRef(0);

  const reducedMotion = useSyncExternalStore(
    subscribeReducedMotion,
    getReducedMotion,
    getReducedMotionServer,
  );
  const [visible, setVisible] = useState(true);
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);

  // Pause when the rail is off-screen (>50% out of view).
  useEffect(() => {
    const node = wrapRef.current;
    if (!node || typeof IntersectionObserver === "undefined") return;
    const obs = new IntersectionObserver(
      (entries) => setVisible(entries[0]?.isIntersecting ?? false),
      { threshold: 0.5 },
    );
    obs.observe(node);
    return () => obs.disconnect();
  }, []);

  // Track user-driven scroll input only (wheel/touch/keyboard); programmatic
  // scrollBy() does not fire these, so we don't pause ourselves.
  useEffect(() => {
    const ul = listRef.current;
    if (!ul) return;
    const mark = () => {
      lastUserScrollAt.current = Date.now();
    };
    ul.addEventListener("wheel", mark, { passive: true });
    ul.addEventListener("touchstart", mark, { passive: true });
    ul.addEventListener("keydown", mark);
    return () => {
      ul.removeEventListener("wheel", mark);
      ul.removeEventListener("touchstart", mark);
      ul.removeEventListener("keydown", mark);
    };
  }, []);

  const canAutoplay =
    !reducedMotion && visible && !hovered && !focused && items.length > 1;

  const scrollByStep = (dir: 1 | -1) => {
    const ul = listRef.current;
    if (!ul) return;
    const max = ul.scrollWidth - ul.clientWidth;
    const cur = ul.scrollLeft;
    let next = cur + dir * STEP;
    if (dir > 0 && cur >= max - 4) next = 0;
    else if (dir < 0 && cur <= 4) next = max;
    ul.scrollTo({ left: next, behavior: "smooth" });
  };

  useEffect(() => {
    if (!canAutoplay) return;
    const id = window.setInterval(() => {
      if (Date.now() - lastUserScrollAt.current < USER_SCROLL_GRACE_MS) return;
      scrollByStep(1);
    }, ADVANCE_MS);
    return () => window.clearInterval(id);
  }, [canAutoplay]);

  return (
    <div
      className="space-y-3"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onFocusCapture={() => setFocused(true)}
      onBlurCapture={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setFocused(false);
      }}
    >
      <div
        ref={wrapRef}
        className="relative -mx-6 px-6 md:-mx-16 md:px-16"
        style={{
          WebkitMaskImage:
            "linear-gradient(to right, transparent 0, black 40px, black calc(100% - 40px), transparent 100%)",
          maskImage:
            "linear-gradient(to right, transparent 0, black 40px, black calc(100% - 40px), transparent 100%)",
        }}
      >
        <ul
          ref={listRef}
          role="list"
          aria-label="All live scholarships"
          aria-live="off"
          className="flex gap-4 overflow-x-auto pb-4"
          style={{ scrollSnapType: "x mandatory", scrollPaddingInline: "24px" }}
        >
          {q.isLoading ? (
            <RailSkeleton />
          ) : items.length === 0 ? (
            <li className="py-4 text-[14px] text-ink-muted">No scholarships available right now.</li>
          ) : (
            items.map((s) => <RailCard key={s.scholarship_id} s={s} />)
          )}
        </ul>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => scrollByStep(-1)}
            disabled={items.length === 0}
            aria-label="Previous scholarships"
            className="inline-flex size-11 items-center justify-center rounded-full border border-[var(--color-border)] bg-paper-white text-ink-muted transition-colors hover:bg-paper-warm hover:text-ink-deep focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)] disabled:pointer-events-none disabled:opacity-40"
          >
            <ChevronLeft className="size-5" strokeWidth={1.5} />
          </button>
          <button
            type="button"
            onClick={() => scrollByStep(1)}
            disabled={items.length === 0}
            aria-label="Next scholarships"
            className="inline-flex size-11 items-center justify-center rounded-full border border-[var(--color-border)] bg-paper-white text-ink-muted transition-colors hover:bg-paper-warm hover:text-ink-deep focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)] disabled:pointer-events-none disabled:opacity-40"
          >
            <ChevronRight className="size-5" strokeWidth={1.5} />
          </button>
        </div>
        <Button asChild variant="link" size="sm">
          <Link href="/discover">
            Browse all scholarships <ArrowRight className="ml-1 size-3.5" strokeWidth={1.5} />
          </Link>
        </Button>
      </div>
    </div>
  );
}
