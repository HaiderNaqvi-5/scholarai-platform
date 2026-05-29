"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, CalendarRange, Globe } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { endpoints } from "@/lib/api";
import type { ScholarshipListItem } from "@/lib/api";

function formatDeadline(iso: string | null): string {
  if (!iso) return "Rolling deadline";
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

function RailCard({ s }: { s: ScholarshipListItem }) {
  return (
    <li
      className="flex w-[280px] shrink-0 flex-col justify-between rounded-[20px] border border-[var(--color-border)] bg-paper-white p-5 transition-shadow duration-150 hover:shadow-[0_4px_20px_-8px_oklch(0.14_0.04_218/0.12)]"
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

  return (
    <div className="space-y-4">
      <div
        className="relative -mx-6 px-6 md:-mx-16 md:px-16"
        style={{
          WebkitMaskImage:
            "linear-gradient(to right, transparent 0, black 40px, black calc(100% - 40px), transparent 100%)",
          maskImage:
            "linear-gradient(to right, transparent 0, black 40px, black calc(100% - 40px), transparent 100%)",
        }}
      >
        <ul
          role="list"
          aria-label="All live scholarships"
          tabIndex={0}
          className="flex gap-4 overflow-x-auto pb-4 outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-lapis"
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

      <div className="flex justify-end">
        <Button asChild variant="link" size="sm">
          <Link href="/discover">
            Browse all scholarships <ArrowRight className="ml-1 size-3.5" strokeWidth={1.5} />
          </Link>
        </Button>
      </div>
    </div>
  );
}
