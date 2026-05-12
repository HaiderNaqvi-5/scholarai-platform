"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Play, RotateCcw } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { endpoints } from "@/lib/api";
import type { IngestionRun, IngestionRunStatus } from "@/lib/api";

const STATUSES: { code: IngestionRunStatus | ""; label: string }[] = [
  { code: "", label: "All" },
  { code: "queued", label: "Queued" },
  { code: "running", label: "Running" },
  { code: "succeeded", label: "Succeeded" },
  { code: "failed", label: "Failed" },
];

const TONE: Record<IngestionRunStatus, "neutral" | "validated" | "caution" | "danger"> = {
  queued: "neutral",
  running: "caution",
  succeeded: "validated",
  failed: "danger",
};

function IngestionInner() {
  const router = useRouter();
  const sp = useSearchParams();
  const status = (sp.get("status") as IngestionRunStatus | null) ?? undefined;
  const qc = useQueryClient();

  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [sourceKey, setSourceKey] = useState("");

  const runsQ = useQuery({
    queryKey: ["ingestion", "runs", status],
    queryFn: () => endpoints.curation.listRuns({ status, page_size: 50 }),
    refetchInterval: 10_000,
  });

  const start = useMutation({
    mutationFn: () => endpoints.curation.startRun({ source_key: sourceKey.trim() }),
    onSuccess: () => {
      toast.success("Run started.");
      setSourceKey("");
      qc.invalidateQueries({ queryKey: ["ingestion", "runs"] });
    },
    onError: () => toast.error("Couldn't start run."),
  });

  const bulkRetry = useMutation({
    mutationFn: () => endpoints.curation.bulkRetry(Array.from(selected)),
    onSuccess: (data) => {
      toast.success(`Retried ${data.success_count}. ${data.failed_ids.length} failed.`);
      setSelected(new Set());
      qc.invalidateQueries({ queryKey: ["ingestion", "runs"] });
    },
    onError: () => toast.error("Bulk retry failed."),
  });

  const setStatusFilter = (v: string) => {
    const next = new URLSearchParams(sp.toString());
    if (v) next.set("status", v);
    else next.delete("status");
    router.replace(`/admin/ingestion${next.toString() ? `?${next.toString()}` : ""}`);
  };

  const toggleSelect = (id: string) => {
    setSelected((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <header>
        <h1 className="font-display text-3xl text-ink">Ingestion runs</h1>
        <p className="mt-1 text-ink-muted">Source registry runs, capture, retries, and snapshots.</p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Start a run</CardTitle>
        </CardHeader>
        <CardBody>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (sourceKey.trim()) start.mutate();
            }}
            className="flex items-center gap-2"
          >
            <Input
              value={sourceKey}
              onChange={(e) => setSourceKey(e.target.value)}
              placeholder="source_key (e.g. scholarships_can_msc)"
              className="max-w-sm"
            />
            <Button type="submit" loading={start.isPending} disabled={!sourceKey.trim()}>
              <Play className="size-4" strokeWidth={2} /> Start
            </Button>
          </form>
        </CardBody>
      </Card>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          {STATUSES.map((s) => (
            <button
              key={s.code}
              type="button"
              onClick={() => setStatusFilter(s.code)}
              className={`h-9 rounded-full px-3 text-sm transition-colors duration-150 ${
                (status ?? "") === s.code
                  ? "bg-ink text-paper"
                  : "border border-[var(--color-border)] bg-paper-white text-ink hover:bg-paper-warm"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
        {selected.size > 0 ? (
          <Button
            variant="secondary"
            onClick={() => bulkRetry.mutate()}
            loading={bulkRetry.isPending}
          >
            <RotateCcw className="size-4" strokeWidth={2} /> Retry {selected.size}
          </Button>
        ) : null}
      </div>

      {runsQ.isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : !runsQ.data || runsQ.data.items.length === 0 ? (
        <div className="rounded-[20px] border border-[var(--color-border)] bg-paper-white p-10 text-center">
          <p className="font-display text-ink">No runs match.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-[16px] border border-[var(--color-border)] bg-paper-white">
          <table className="w-full text-sm">
            <thead className="border-b border-[var(--color-border)] bg-paper-warm/40 text-left text-xs uppercase tracking-wider text-ink-subtle">
              <tr>
                <th className="w-10 px-3 py-2"></th>
                <th className="px-3 py-2">Source</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Records</th>
                <th className="px-3 py-2">Started</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {runsQ.data.items.map((r: IngestionRun) => (
                <tr
                  key={r.run_id}
                  className="border-b border-[var(--color-border)] last:border-b-0 hover:bg-paper-warm/30"
                >
                  <td className="px-3 py-2">
                    <input
                      type="checkbox"
                      aria-label={`Select run ${r.run_id}`}
                      checked={selected.has(r.run_id)}
                      onChange={() => toggleSelect(r.run_id)}
                    />
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-ink">{r.source_key}</td>
                  <td className="px-3 py-2">
                    <Badge tone={TONE[r.status]}>{r.status}</Badge>
                  </td>
                  <td className="px-3 py-2 font-mono text-ink">{r.records_found ?? "—"}</td>
                  <td className="px-3 py-2 text-ink-muted">
                    {new Date(r.started_at).toLocaleString()}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <Link
                      href={`/admin/ingestion/${r.run_id}`}
                      className="inline-flex items-center gap-1 text-sm text-ink-muted hover:text-ink"
                    >
                      Open <ArrowRight className="size-3" strokeWidth={2} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default function IngestionListPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
      <IngestionInner />
    </Suspense>
  );
}
