"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/ui/section-header";
import { endpoints } from "@/lib/api";

export default function MentorQueuePage() {
  const queueQ = useQuery({
    queryKey: ["mentor", "pending"],
    queryFn: () => endpoints.mentors.pending(40),
  });

  return (
    <div data-testid="mentor-queue" className="mx-auto max-w-4xl">
      <PageHeader
        title="Pending reviews"
        description={
          queueQ.data
            ? `${queueQ.data.total} document${queueQ.data.total === 1 ? "" : "s"} waiting.`
            : "Documents waiting for human review."
        }
        className="mb-6"
      />

      {queueQ.isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      ) : queueQ.isError ? (
        <Empty title="Couldn't load queue." body="Try again." />
      ) : !queueQ.data || queueQ.data.items.length === 0 ? (
        <Empty title="Queue empty" body="Nothing waiting for human review right now." />
      ) : (
        <ul className="space-y-3">
          {queueQ.data.items.map((d) => (
            <li key={d.id}>
              <Link href={`/mentor/documents/${d.id}`} className="block">
                <Card className="hover:border-ink-muted">
                  <CardHeader className="flex-row items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <FileText className="mt-1 size-5 text-ink-muted" strokeWidth={2} />
                      <div>
                        <CardTitle>{d.title}</CardTitle>
                        <p className="mt-1 text-sm text-ink-muted">
                          {d.document_type} · Submitted{" "}
                          {new Date(d.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge tone="caution">Pending</Badge>
                      <ArrowRight className="size-4 text-ink-subtle" strokeWidth={2} />
                    </div>
                  </CardHeader>
                  {d.scholarship_ids && d.scholarship_ids.length > 0 ? (
                    <CardBody>
                      <p className="text-xs text-ink-subtle">
                        Grounded against {d.scholarship_ids.length} scholarship
                        {d.scholarship_ids.length === 1 ? "" : "s"}
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

function Empty({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-[20px] border border-[var(--color-border)] bg-paper-white p-10 text-center">
      <h2 className="font-display text-xl text-ink">{title}</h2>
      <p className="mt-2 text-ink-muted">{body}</p>
    </div>
  );
}
