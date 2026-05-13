"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, RotateCcw, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { endpoints } from "@/lib/api";
import type { IngestionRunStatus } from "@/lib/api";

const TONE: Record<IngestionRunStatus, "neutral" | "validated" | "caution" | "danger"> = {
  queued: "neutral",
  running: "caution",
  succeeded: "validated",
  failed: "danger",
};

export default function IngestionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const qc = useQueryClient();
  const [showSnapshot, setShowSnapshot] = useState(false);

  const runQ = useQuery({
    queryKey: ["ingestion", "run", id],
    queryFn: () => endpoints.curation.runDetail(id),
    refetchInterval: (q) =>
      q.state.data?.status === "running" || q.state.data?.status === "queued" ? 5000 : false,
  });

  const snapshotQ = useQuery({
    queryKey: ["ingestion", "run", id, "snapshot"],
    queryFn: () => endpoints.curation.snapshot(id),
    enabled: showSnapshot && !!runQ.data?.capture_path,
  });

  const retry = useMutation({
    mutationFn: () => endpoints.curation.retryRun(id),
    onSuccess: () => {
      toast.success("Retry queued.");
      qc.invalidateQueries({ queryKey: ["ingestion", "run", id] });
    },
    onError: () => toast.error("Couldn't retry."),
  });

  const clearSnap = useMutation({
    mutationFn: () => endpoints.curation.clearSnapshot(id),
    onSuccess: () => {
      toast.success("Snapshot cleared.");
      qc.invalidateQueries({ queryKey: ["ingestion", "run", id] });
      setShowSnapshot(false);
    },
    onError: () => toast.error("Couldn't clear snapshot."),
  });

  if (runQ.isLoading) {
    return (
      <div className="mx-auto max-w-4xl space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  if (runQ.isError || !runQ.data) {
    return (
      <div className="mx-auto max-w-3xl rounded-[20px] border border-[var(--color-border)] bg-paper-white p-10 text-center">
        <h2 className="font-display text-xl text-ink">Run not found.</h2>
      </div>
    );
  }

  const run = runQ.data;

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <Link
        href="/admin/ingestion"
        className="inline-flex items-center gap-1 text-sm text-ink-muted hover:text-ink"
      >
        <ArrowLeft className="size-4" strokeWidth={2} /> Ingestion
      </Link>

      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-mono text-xl text-ink">{run.source_key}</h1>
          <p className="mt-1 text-sm text-ink-muted">
            Run {run.run_id} · Started {new Date(run.started_at).toLocaleString()}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge tone={TONE[run.status]}>{run.status}</Badge>
          <Button variant="secondary" onClick={() => retry.mutate()} loading={retry.isPending}>
            <RotateCcw className="size-4" strokeWidth={2} /> Retry
          </Button>
        </div>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Diagnostics</CardTitle>
        </CardHeader>
        <CardBody className="space-y-2 text-sm">
          <Row label="Records found" value={run.records_found?.toString() ?? "—"} />
          <Row label="Execution mode" value={run.execution_mode_selected ?? "—"} />
          <Row label="Dispatch status" value={run.dispatch_status ?? "—"} />
          <Row label="Failure phase" value={run.failure_phase ?? "—"} />
          <Row
            label="Finished at"
            value={run.finished_at ? new Date(run.finished_at).toLocaleString() : "—"}
          />
          <Row label="Capture path" value={run.capture_path ?? "—"} />
        </CardBody>
      </Card>

      {run.capture_path ? (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <div>
                <CardTitle>Captured HTML snapshot</CardTitle>
                <CardDescription>Raw page content captured during this run.</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setShowSnapshot((v) => !v)}
                >
                  {showSnapshot ? "Hide" : "View"}
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => clearSnap.mutate()}
                  aria-label="Clear snapshot"
                  disabled={clearSnap.isPending}
                >
                  <Trash2 className="size-4" strokeWidth={2} />
                </Button>
              </div>
            </div>
          </CardHeader>
          {showSnapshot ? (
            <CardBody>
              {snapshotQ.isLoading ? (
                <Skeleton className="h-48 w-full" />
              ) : snapshotQ.data ? (
                <>
                  <p className="text-xs text-ink-subtle">
                    Captured {new Date(snapshotQ.data.captured_at).toLocaleString()} ·{" "}
                    {snapshotQ.data.content_length} chars
                  </p>
                  <pre className="mt-2 max-h-96 overflow-auto rounded-[8px] bg-paper-warm/40 p-3 font-mono text-xs text-ink">
                    {snapshotQ.data.html_content}
                  </pre>
                </>
              ) : (
                <p className="text-sm text-ink-subtle">Couldn&apos;t load snapshot.</p>
              )}
            </CardBody>
          ) : null}
        </Card>
      ) : null}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-[var(--color-border)] pb-2 last:border-b-0 last:pb-0">
      <span className="font-mono text-xs uppercase tracking-wider text-ink-subtle">{label}</span>
      <span className="break-all text-right font-mono text-ink">{value}</span>
    </div>
  );
}
