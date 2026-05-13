"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { endpoints } from "@/lib/api";
import type { CurationState } from "@/lib/api";

const STATES: { code: CurationState | ""; label: string }[] = [
  { code: "", label: "All" },
  { code: "raw", label: "Raw" },
  { code: "validated", label: "Validated" },
  { code: "published", label: "Published" },
];

const TONE: Record<CurationState, "neutral" | "validated" | "caution"> = {
  raw: "caution",
  validated: "neutral",
  published: "validated",
};

function CurationInner() {
  const router = useRouter();
  const sp = useSearchParams();
  const state = (sp.get("state") as CurationState | null) ?? undefined;

  const recordsQ = useQuery({
    queryKey: ["curation", "records", state],
    queryFn: () => endpoints.curation.listRecords({ state, page_size: 50 }),
  });

  const setState = (v: string) => {
    const next = new URLSearchParams(sp.toString());
    if (v) next.set("state", v);
    else next.delete("state");
    router.replace(`/admin/curation${next.toString() ? `?${next.toString()}` : ""}`);
  };

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <header>
        <h1 className="font-display text-3xl text-ink">Curation</h1>
        <p className="mt-1 text-ink-muted">
          State machine: raw → validated → published. Public discover shows published only.
        </p>
      </header>

      <div className="flex flex-wrap gap-2">
        {STATES.map((s) => (
          <button
            key={s.code}
            type="button"
            onClick={() => setState(s.code)}
            className={`h-9 rounded-full px-3 text-sm transition-colors duration-150 ${
              (state ?? "") === s.code
                ? "bg-ink text-paper"
                : "border border-[var(--color-border)] bg-paper-white text-ink hover:bg-paper-warm"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {recordsQ.isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : !recordsQ.data || recordsQ.data.items.length === 0 ? (
        <div className="rounded-[20px] border border-[var(--color-border)] bg-paper-white p-10 text-center">
          <p className="font-display text-ink">No records.</p>
        </div>
      ) : (
        <ul className="space-y-3">
          {recordsQ.data.items.map((r) => (
            <li key={r.record_id}>
              <Link href={`/admin/curation/${r.record_id}`} className="block">
                <Card className="hover:border-ink-muted">
                  <CardHeader className="flex-row items-start justify-between gap-4">
                    <div>
                      <CardTitle>{r.title}</CardTitle>
                      <p className="mt-1 font-mono text-xs text-ink-subtle">{r.record_id}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge tone={TONE[r.state]}>{r.state}</Badge>
                      <ArrowRight className="size-4 text-ink-subtle" strokeWidth={2} />
                    </div>
                  </CardHeader>
                  {r.audit_log.length > 0 ? (
                    <CardBody>
                      <p className="text-xs text-ink-subtle">
                        Last action: {r.audit_log[r.audit_log.length - 1].action} by{" "}
                        {r.audit_log[r.audit_log.length - 1].actor}
                      </p>
                    </CardBody>
                  ) : null}
                </Card>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function CurationListPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
      <CurationInner />
    </Suspense>
  );
}
