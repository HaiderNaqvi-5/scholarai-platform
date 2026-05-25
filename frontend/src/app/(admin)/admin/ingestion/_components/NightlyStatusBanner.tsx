"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Clock } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { endpoints } from "@/lib/api";
import type { SourceHealthSummary } from "@/lib/api";

const HEALTH_TONE: Record<string, "validated" | "caution" | "danger" | "neutral"> = {
  healthy: "validated",
  degraded: "caution",
  down: "danger",
  unknown: "neutral",
};

function formatRelative(iso: string | null | undefined): string {
  if (!iso) return "never";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  const diffMin = Math.round((Date.now() - then) / 60_000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 48) return `${diffHr}h ago`;
  return `${Math.round(diffHr / 24)}d ago`;
}

function formatEta(iso: string): string {
  const then = new Date(iso);
  if (Number.isNaN(then.getTime())) return "—";
  const diffMin = Math.round((then.getTime() - Date.now()) / 60_000);
  if (diffMin < 60) return `in ${diffMin}m`;
  const diffHr = Math.round(diffMin / 60);
  return `in ${diffHr}h`;
}

export function NightlyStatusBanner() {
  const q = useQuery({
    queryKey: ["ingestion", "nightly-status"],
    queryFn: () => endpoints.curation.nightlyStatus(),
    refetchInterval: 30_000,
  });

  if (q.isLoading) {
    return <Skeleton className="h-32 w-full" />;
  }
  if (q.isError || !q.data) {
    return null;
  }

  const d = q.data;
  const StatusIcon = d.is_stale ? AlertTriangle : CheckCircle2;
  const statusTone = d.is_stale ? "danger" : "validated";
  const hoursSince =
    d.hours_since_last_completion != null
      ? d.hours_since_last_completion.toFixed(1)
      : null;

  return (
    <Card data-testid="nightly-status-banner">
      <CardBody className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <StatusIcon
              className={`size-5 mt-0.5 ${
                d.is_stale ? "text-sindoor" : "text-validated"
              }`}
              strokeWidth={2}
            />
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-display text-lg text-ink">Nightly ingestion</h2>
                <Badge tone={statusTone}>{d.is_stale ? "Stale" : "Healthy"}</Badge>
              </div>
              <p className="mt-1 text-sm text-ink-subtle">
                Last completed{" "}
                <span className="font-mono text-ink">
                  {formatRelative(d.last_completed_at)}
                </span>
                {hoursSince != null ? (
                  <>
                    {" "}
                    (<span className="font-mono">{hoursSince}h</span>, threshold{" "}
                    <span className="font-mono">{d.stale_threshold_hours}h</span>)
                  </>
                ) : null}
                {" · "}
                <Clock className="inline size-3.5 align-text-bottom" />
                {" "}next run <span className="font-mono">{formatEta(d.next_expected_at)}</span>
              </p>
            </div>
          </div>
          <div className="text-right text-xs text-ink-subtle">
            <div>
              <span className="font-mono text-ink">{d.active_source_count}</span> active
              sources
            </div>
            <div>
              stagger <span className="font-mono">{Math.round(d.stagger_seconds / 60)}m</span>
            </div>
          </div>
        </div>

        {d.sources.length > 0 ? (
          <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {d.sources.map((s: SourceHealthSummary) => (
              <li
                key={s.source_key}
                className="flex items-center justify-between gap-2 rounded-[12px] border border-[var(--color-border)] bg-paper-warm/30 px-3 py-2"
              >
                <div className="min-w-0">
                  <div className="truncate text-sm text-ink">{s.display_name}</div>
                  <div className="truncate text-xs text-ink-subtle">
                    success {formatRelative(s.last_success_at)}
                    {s.consecutive_failures > 0 ? (
                      <>
                        {" · "}
                        <span className="text-sindoor">
                          {s.consecutive_failures} fail
                          {s.consecutive_failures === 1 ? "" : "s"}
                        </span>
                      </>
                    ) : null}
                  </div>
                </div>
                <Badge tone={HEALTH_TONE[s.health_status] ?? "neutral"}>
                  {s.health_status}
                </Badge>
              </li>
            ))}
          </ul>
        ) : null}
      </CardBody>
    </Card>
  );
}
