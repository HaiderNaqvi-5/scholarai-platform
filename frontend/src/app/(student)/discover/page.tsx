"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Search, X } from "lucide-react";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ScholarshipCard } from "@/components/scholarship/ScholarshipCard";
import { Pagination } from "@/components/ui/pagination";
import { endpoints } from "@/lib/api";
import type { ScholarshipFilters } from "@/lib/api/endpoints/scholarships";
import type { SavedOpportunity } from "@/lib/api";

const COUNTRIES = [
  { code: "", label: "Any country" },
  { code: "CA", label: "Canada" },
  { code: "US", label: "United States" },
  { code: "UK", label: "United Kingdom" },
  { code: "AU", label: "Australia" },
  { code: "DE", label: "Germany" },
];

const DEGREES = [
  { code: "", label: "Any degree" },
  { code: "BS", label: "Bachelor's" },
  { code: "MS", label: "Master's" },
  { code: "PHD", label: "PhD" },
];

const FUNDING = [
  { code: "", label: "Any funding" },
  { code: "TUITION", label: "Tuition" },
  { code: "TUITION_STIPEND", label: "Tuition + stipend" },
  { code: "FULL", label: "Full ride" },
  { code: "TRAVEL", label: "Travel" },
];

const SORTS = [
  { code: "deadline", label: "Deadline" },
  { code: "recent", label: "Newest" },
  { code: "title", label: "Title" },
];

const DEADLINES = [
  { code: "", label: "Any deadline" },
  { code: "30", label: "Within 30d" },
  { code: "90", label: "Within 90d" },
  { code: "180", label: "Within 6mo" },
];

function paramsToFilters(p: URLSearchParams): ScholarshipFilters {
  return {
    query: p.get("q") ?? undefined,
    country_code: p.get("country") ?? undefined,
    degree_level: p.get("degree") ?? undefined,
    field_tag: p.get("field") ?? undefined,
    funding_type: p.get("funding") ?? undefined,
    deadline_within_days: p.get("dl") ? Number(p.get("dl")) : undefined,
    sort: (p.get("sort") as ScholarshipFilters["sort"]) ?? "deadline",
    page: p.get("page") ? Number(p.get("page")) : 1,
    page_size: 20,
  };
}

function DiscoverInner() {
  const router = useRouter();
  const sp = useSearchParams();
  const filters = useMemo(() => paramsToFilters(sp), [sp]);
  const [q, setQ] = useState(filters.query ?? "");

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setQ(filters.query ?? "");
  }, [filters.query]);

  const update = useCallback(
    (patch: Record<string, string | undefined>) => {
      const next = new URLSearchParams(sp.toString());
      Object.entries(patch).forEach(([k, v]) => {
        if (!v) next.delete(k);
        else next.set(k, v);
      });
      next.delete("page");
      router.replace(`/discover${next.toString() ? `?${next.toString()}` : ""}`);
    },
    [router, sp],
  );

  const listQ = useQuery({
    queryKey: ["scholarships", filters],
    queryFn: () => endpoints.scholarships.list(filters),
  });

  const savedQ = useQuery({
    queryKey: ["saved"],
    queryFn: endpoints.saved.list,
  });
  const savedSet = useMemo(
    () => new Set(savedQ.data?.items.map((s) => s.scholarship_id) ?? []),
    [savedQ.data],
  );

  const qc = useQueryClient();
  const toggleSave = useMutation({
    mutationFn: async ({ id, currentlySaved }: { id: string; currentlySaved: boolean }) => {
      if (currentlySaved) await endpoints.saved.remove(id);
      else await endpoints.saved.add(id);
      return { id, currentlySaved };
    },
    onMutate: async ({ id, currentlySaved }) => {
      await qc.cancelQueries({ queryKey: ["saved"] });
      const prev = qc.getQueryData<{ items: SavedOpportunity[] }>(["saved"]);
      qc.setQueryData<{ items: SavedOpportunity[] } | undefined>(["saved"], (old) => {
        if (!old) return old;
        if (currentlySaved) {
          return { items: old.items.filter((s) => s.scholarship_id !== id) };
        }
        const sch = listQ.data?.items.find((x) => x.id === id);
        if (!sch) return old;
        return {
          items: [
            ...old.items,
            {
              scholarship_id: id,
              scholarship: sch,
              status: "saved" as const,
              saved_at: new Date().toISOString(),
            },
          ],
        };
      });
      return { prev };
    },
    onError: (_e, _v, ctx) => {
      qc.setQueryData(["saved"], ctx?.prev);
      toast.error("Couldn't update saved list.");
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ["saved"] }),
  });

  const onSearch = (e: React.FormEvent) => {
    e.preventDefault();
    update({ q });
  };

  const clearAll = () => router.replace("/discover");
  const hasFilters = sp.toString().length > 0;

  const goPage = (next: number) => {
    const params = new URLSearchParams(sp.toString());
    if (next <= 1) params.delete("page");
    else params.set("page", String(next));
    router.replace(`/discover${params.toString() ? `?${params.toString()}` : ""}`);
  };

  return (
    <div className="mx-auto max-w-[1024px]" data-testid="discover-grid">
      <header className="mb-4">
        <h1 className="font-display text-[32px] italic font-[450] leading-[1.1] tracking-[-0.02em] text-ink-deep">
          Discover
        </h1>
        <p className="mt-1 text-[14px] text-ink-muted">
          {listQ.data ? `${listQ.data.total} published scholarships.` : "All published scholarships."}
        </p>
      </header>

      <div className="sticky top-[calc(var(--topbar-h,56px))] z-10 -mx-4 mb-5 border-b border-[var(--color-border)] bg-paper/95 px-4 py-3 backdrop-blur md:-mx-6 md:px-6">
        <form onSubmit={onSearch} className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-ink-subtle" strokeWidth={2} />
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search title, provider…"
              className="pl-9"
              aria-label="Search scholarships"
            />
          </div>
          <Button type="submit" variant="secondary">
            Search
          </Button>
          {hasFilters ? (
            <Button type="button" variant="ghost" onClick={clearAll} aria-label="Clear filters">
              <X className="size-4" strokeWidth={2} /> Clear
            </Button>
          ) : null}
        </form>
        <div className="mt-3 flex flex-wrap gap-2">
          <FilterSelect
            label="Country"
            value={filters.country_code ?? ""}
            options={COUNTRIES}
            onChange={(v) => update({ country: v })}
          />
          <FilterSelect
            label="Degree"
            value={filters.degree_level ?? ""}
            options={DEGREES}
            onChange={(v) => update({ degree: v })}
          />
          <FilterSelect
            label="Funding"
            value={filters.funding_type ?? ""}
            options={FUNDING}
            onChange={(v) => update({ funding: v })}
          />
          <FilterSelect
            label="Deadline"
            value={filters.deadline_within_days ? String(filters.deadline_within_days) : ""}
            options={DEADLINES}
            onChange={(v) => update({ dl: v })}
          />
          <FilterSelect
            label="Sort"
            value={filters.sort ?? "deadline"}
            options={SORTS}
            onChange={(v) => update({ sort: v })}
          />
        </div>
      </div>

      {listQ.isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-36 w-full" />
          ))}
        </div>
      ) : listQ.isError ? (
        <EmptyBlock
          title="Couldn't load scholarships."
          body="Connection or server issue."
          action={
            <Button onClick={() => listQ.refetch()}>Retry</Button>
          }
        />
      ) : !listQ.data || listQ.data.items.length === 0 ? (
        <EmptyBlock
          title="No matches"
          body="Loosen the filters or clear them to see everything."
          action={hasFilters ? <Button variant="secondary" onClick={clearAll}>Clear filters</Button> : null}
        />
      ) : (
        <>
          <ul className="space-y-3">
            {listQ.data.items.map((s) => (
              <li key={s.id}>
                <ScholarshipCard
                  scholarship={s}
                  saved={savedSet.has(s.id)}
                  saving={toggleSave.isPending && toggleSave.variables?.id === s.id}
                  onToggleSave={() =>
                    toggleSave.mutate({ id: s.id, currentlySaved: savedSet.has(s.id) })
                  }
                />
              </li>
            ))}
          </ul>
          <Pagination
            page={filters.page ?? 1}
            pageSize={filters.page_size ?? 20}
            total={listQ.data.total}
            onChange={goPage}
          />
        </>
      )}
    </div>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: { code: string; label: string }[];
  onChange: (v: string) => void;
}) {
  return (
    <label className="flex items-center gap-2 text-xs text-ink-subtle">
      <span className="uppercase tracking-wider">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-9 rounded-[10px] border border-[var(--color-border)] bg-paper-white px-2 text-sm text-ink"
      >
        {options.map((o) => (
          <option key={o.code} value={o.code}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function EmptyBlock({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="rounded-[20px] border border-[var(--color-border)] bg-paper-white p-10 text-center">
      <h2 className="font-display text-xl text-ink">{title}</h2>
      <p className="mt-2 text-ink-muted">{body}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

export default function DiscoverPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-36 w-full" />
          ))}
        </div>
      }
    >
      <DiscoverInner />
    </Suspense>
  );
}
