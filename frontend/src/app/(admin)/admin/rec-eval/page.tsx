"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Play } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/ui/section-header";
import { endpoints } from "@/lib/api";

type EvalResult = Awaited<ReturnType<typeof endpoints.recommendations.evaluateBenchmark>>;

function metricEntries(m: {
  k: number;
  precision_at_k: number;
  recall_at_k: number;
  ndcg_at_k: number;
  mrr_at_k: number | null;
}): [string, number][] {
  const entries: [string, number][] = [
    [`precision@${m.k}`, m.precision_at_k],
    [`recall@${m.k}`, m.recall_at_k],
    [`ndcg@${m.k}`, m.ndcg_at_k],
  ];
  if (m.mrr_at_k != null) entries.push([`mrr@${m.k}`, m.mrr_at_k]);
  return entries;
}

export default function RecEvalPage() {
  const benchQ = useQuery({
    queryKey: ["recommendations", "benchmarks"],
    queryFn: endpoints.recommendations.benchmarks,
  });

  const [result, setResult] = useState<EvalResult | null>(null);
  const [running, setRunning] = useState<string | null>(null);

  const run = useMutation({
    mutationFn: (datasetId: string) => endpoints.recommendations.evaluateBenchmark(datasetId),
    onMutate: (id) => setRunning(id),
    onSuccess: (data) => {
      setResult(data);
      toast.success("Benchmark complete.");
    },
    onError: () => toast.error("Benchmark failed."),
    onSettled: () => setRunning(null),
  });

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <PageHeader
        title="Recommendation evaluation"
        description="Benchmark datasets — precision@k, recall@k, nDCG@k, MRR@k. Per-case breakdown plus aggregate trends."
      />
      <header className="sr-only">
        <p>
          Benchmark datasets · precision@k, recall@k, nDCG@k, MRR@k. Per-case breakdown plus
          aggregate.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Benchmark datasets</CardTitle>
          <CardDescription>Frozen judged sets used for ranker regression.</CardDescription>
        </CardHeader>
        <CardBody>
          {benchQ.isLoading ? (
            <Skeleton className="h-32 w-full" />
          ) : !benchQ.data || benchQ.data.items.length === 0 ? (
            <p className="text-sm text-ink-subtle">No datasets registered.</p>
          ) : (
            <ul className="space-y-2">
              {benchQ.data.items.map((d) => (
                <li
                  key={d.dataset_id}
                  className="flex items-center justify-between rounded-[12px] border border-[var(--color-border)] bg-paper-white p-3"
                >
                  <div>
                    <p className="font-display text-ink">{d.title}</p>
                    <p className="text-xs text-ink-subtle">
                      {d.dataset_id} · v{d.version} · {d.case_count} cases · k=
                      {d.k_values.join(",")}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => run.mutate(d.dataset_id)}
                    loading={running === d.dataset_id}
                    disabled={running !== null && running !== d.dataset_id}
                  >
                    <Play className="size-4" strokeWidth={2} /> Evaluate
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      {result ? (
        <Card>
          <CardHeader>
            <CardTitle>Result · {result.dataset_id}</CardTitle>
            <CardDescription>
              Pass rate:{" "}
              <Badge tone={result.aggregate.pass_rate >= 0.8 ? "validated" : "caution"}>
                {Math.round(result.aggregate.pass_rate * 100)}%
              </Badge>{" "}
              · {result.aggregate.pass_count}/{result.aggregate.case_count} cases passed
            </CardDescription>
          </CardHeader>
          <CardBody className="space-y-4">
            <div>
              <p className="font-mono text-xs uppercase tracking-wider text-ink-subtle">
                Aggregate (mean over cases)
              </p>
              <ul className="mt-2 grid gap-1 sm:grid-cols-2">
                {result.aggregate.average_metrics.flatMap(metricEntries).map(([label, v]) => (
                  <li
                    key={label}
                    className="flex items-center justify-between rounded-[8px] border border-[var(--color-border)] bg-paper-white px-3 py-1.5 font-mono text-sm"
                  >
                    <span className="text-ink-muted">{label}</span>
                    <span className="text-ink">{v.toFixed(3)}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <p className="font-mono text-xs uppercase tracking-wider text-ink-subtle">
                Per-case ({result.case_results.length})
              </p>
              <div className="mt-2 max-h-96 overflow-auto rounded-[12px] border border-[var(--color-border)]">
                <table className="w-full text-sm">
                  <thead className="bg-paper-warm/40 text-left text-xs uppercase tracking-wider text-ink-subtle">
                    <tr>
                      <th className="px-3 py-2">Case</th>
                      {(result.case_results[0]?.metrics ?? [])
                        .flatMap(metricEntries)
                        .map(([label]) => (
                          <th key={label} className="px-3 py-2">
                            {label}
                          </th>
                        ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.case_results.map((c) => (
                      <tr
                        key={c.case_id}
                        className="border-t border-[var(--color-border)] hover:bg-paper-warm/30"
                      >
                        <td className="px-3 py-2 font-mono text-xs text-ink">{c.case_id}</td>
                        {c.metrics.flatMap(metricEntries).map(([label, v]) => (
                          <td key={label} className="px-3 py-2 font-mono text-ink">
                            {v.toFixed(3)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}
