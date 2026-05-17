"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { ChevronDown, FileText, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/badge";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { PageHeader } from "@/components/ui/section-header";
import { endpoints } from "@/lib/api";
import type { DocumentStatus, DocumentSummary } from "@/lib/api";

type FilterKey = "all" | "sop" | "professor_email" | "strategy_report" | "visa";

const FILTER_LABEL: Record<FilterKey, string> = {
  all: "All",
  sop: "SOPs",
  professor_email: "Professor emails",
  strategy_report: "Strategy reports",
  visa: "Visa transcripts",
};

const FILTER_KEYS: FilterKey[] = ["all", "sop", "professor_email", "strategy_report", "visa"];

const STATUS_LABEL: Record<DocumentStatus, string> = {
  pending: "Draft",
  processing: "Draft",
  completed: "Final",
  failed: "Failed — retry",
};

const STATUS_TONE: Record<DocumentStatus, "neutral" | "validated" | "caution" | "sindoor"> = {
  pending: "caution",
  processing: "caution",
  completed: "validated",
  failed: "sindoor",
};

function matchesFilter(doc: DocumentSummary, filter: FilterKey): boolean {
  if (filter === "all") return true;
  const t = (doc.document_type || "").toLowerCase();
  if (filter === "sop") return t === "sop";
  if (filter === "professor_email") return t === "professor_email";
  if (filter === "strategy_report") return t === "strategy_report";
  if (filter === "visa") return t.startsWith("visa");
  return true;
}

export default function DocumentsPage() {
  const router = useRouter();
  const sp = useSearchParams();
  const initial = (sp.get("type") as FilterKey | null) || "all";
  const [filter, setFilter] = useState<FilterKey>(
    FILTER_KEYS.includes(initial) ? initial : "all",
  );

  const docsQ = useQuery({
    queryKey: ["documents"],
    queryFn: endpoints.documents.list,
  });

  const items = useMemo(() => {
    const all = docsQ.data?.items ?? [];
    return all.filter((d) => matchesFilter(d, filter));
  }, [docsQ.data, filter]);

  const setFilterUrl = (next: FilterKey) => {
    setFilter(next);
    const params = new URLSearchParams(sp.toString());
    if (next === "all") params.delete("type");
    else params.set("type", next);
    router.replace(`/documents${params.toString() ? `?${params.toString()}` : ""}`);
  };

  return (
    <div className="mx-auto max-w-[1024px]">
      <PageHeader title="Documents" actions={<AddMenu />} />

      <div className="mt-6 flex flex-wrap items-center gap-2" role="tablist" aria-label="Filter by type">
        {FILTER_KEYS.map((k) => {
          const active = filter === k;
          return (
            <button
              key={k}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => setFilterUrl(k)}
              className={`h-8 rounded-full px-3 text-[12px] font-medium uppercase tracking-[0.06em] transition-colors ${
                active
                  ? "bg-ink-deep text-paper-white"
                  : "border border-[var(--color-border)] bg-paper-white text-ink-muted hover:bg-paper-warm"
              }`}
            >
              {FILTER_LABEL[k]}
            </button>
          );
        })}
      </div>

      <section className="mt-6" data-testid="documents-list">
        {docsQ.isLoading ? (
          <div className="space-y-3" aria-busy>
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-[96px] w-full rounded-[18px]" />
            ))}
          </div>
        ) : docsQ.isError ? (
          <ErrorState
            title="Couldn't load your documents."
            description="Try again in a moment."
            action={<Button onClick={() => docsQ.refetch()}>Retry</Button>}
          />
        ) : items.length === 0 ? (
          <EmptyState
            icon={<FileText className="size-8" strokeWidth={1.5} />}
            title="No documents yet."
            description="Draft your first SOP or professor email to start building your library."
            action={
              <Button asChild>
                <Link href="/documents/sop">Draft SOP</Link>
              </Button>
            }
          />
        ) : (
          <>
            <DesktopTable items={items} />
            <MobileList items={items} />
          </>
        )}
      </section>
    </div>
  );
}

function AddMenu() {
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <Button>
          <Plus className="size-4" strokeWidth={1.5} aria-hidden /> Draft new
          <ChevronDown className="ml-1 size-4" strokeWidth={1.5} aria-hidden />
        </Button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          sideOffset={6}
          className="z-50 min-w-[220px] rounded-[12px] border border-[var(--color-border)] bg-paper-white p-1 shadow-[var(--shadow-raised)]"
        >
          <DropdownMenu.Item asChild>
            <Link
              href="/documents/sop"
              className="flex items-center rounded-[8px] px-3 py-2 text-[13px] text-ink-deep hover:bg-paper-warm focus-visible:outline-none focus-visible:bg-paper-warm"
            >
              Draft SOP
            </Link>
          </DropdownMenu.Item>
          <DropdownMenu.Item asChild>
            <Link
              href="/documents/professor-email"
              className="flex items-center rounded-[8px] px-3 py-2 text-[13px] text-ink-deep hover:bg-paper-warm focus-visible:outline-none focus-visible:bg-paper-warm"
            >
              Draft professor email
            </Link>
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}

function DesktopTable({ items }: { items: DocumentSummary[] }) {
  return (
    <table className="hidden w-full border-collapse text-left lg:table">
      <caption className="sr-only">Your generated documents</caption>
      <thead>
        <tr className="border-b border-[var(--color-border)] font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
          <th scope="col" className="py-2 pr-4">
            Title
          </th>
          <th scope="col" className="py-2 pr-4">
            Type
          </th>
          <th scope="col" className="py-2 pr-4">
            Status
          </th>
          <th scope="col" className="py-2 pr-4">
            Updated
          </th>
          <th scope="col" className="py-2 text-right">
            Open
          </th>
        </tr>
      </thead>
      <tbody>
        {items.map((d) => (
          <tr
            key={d.id}
            className="border-b border-[var(--color-border-quiet)] last:border-b-0 hover:bg-paper-warm/50"
          >
            <td className="py-3 pr-4">
              <Link
                href={`/documents/${d.id}`}
                className="text-[14px] font-medium text-ink-deep hover:underline underline-offset-4"
              >
                {d.title}
              </Link>
            </td>
            <td className="py-3 pr-4 font-mono text-[12px] text-ink-muted">{d.document_type}</td>
            <td className="py-3 pr-4">
              <Chip tone={STATUS_TONE[d.processing_status]}>{STATUS_LABEL[d.processing_status]}</Chip>
            </td>
            <td className="py-3 pr-4 font-mono text-[12px] text-ink-muted">
              {new Date(d.updated_at ?? d.created_at).toLocaleDateString("en-GB", {
                year: "numeric",
                month: "short",
                day: "numeric",
              })}
            </td>
            <td className="py-3 text-right">
              <Link href={`/documents/${d.id}`} className="text-[13px] text-lapis underline underline-offset-2">
                Open
              </Link>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function MobileList({ items }: { items: DocumentSummary[] }) {
  return (
    <ul className="space-y-3 lg:hidden">
      {items.map((d) => (
        <li key={d.id}>
          <Link href={`/documents/${d.id}`} className="block">
            <Card hoverable className="hover:border-ink-muted/40">
              <CardHeader className="flex-row items-start justify-between gap-3">
                <div className="min-w-0">
                  <CardTitle>{d.title}</CardTitle>
                  <p className="mt-1 font-mono text-[12px] text-ink-muted">
                    {d.document_type} · {STATUS_LABEL[d.processing_status]}
                  </p>
                </div>
                <Chip tone={STATUS_TONE[d.processing_status]}>{STATUS_LABEL[d.processing_status]}</Chip>
              </CardHeader>
              <CardBody>
                <p className="font-mono text-[12px] text-ink-subtle">
                  Updated{" "}
                  {new Date(d.updated_at ?? d.created_at).toLocaleDateString("en-GB", {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                  })}
                </p>
              </CardBody>
            </Card>
          </Link>
        </li>
      ))}
    </ul>
  );
}
