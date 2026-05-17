"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { MessageSquare, Plane } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { Chip } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { PageHeader } from "@/components/ui/section-header";
import { TrendStrip } from "@/components/interview/TrendStrip";
import { endpoints } from "@/lib/api";

function InterviewsInner() {
  const analyticsQ = useQuery({
    queryKey: ["interviews", "analytics"],
    queryFn: endpoints.interviews.analytics,
  });

  return (
    <div className="mx-auto max-w-[1024px]" data-testid="interviews-list">
      <PageHeader
        title="Interviews"
        description="Practice country-specific visa questions, or run generic admissions prep."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button asChild>
              <Link href="/interviews/visa">
                <Plane className="size-4" strokeWidth={1.5} aria-hidden /> Practice visa
              </Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/interviews?new=general">
                <MessageSquare className="size-4" strokeWidth={1.5} aria-hidden /> Practice generic
              </Link>
            </Button>
          </div>
        }
      />

      <section className="mt-6 space-y-6">
        {analyticsQ.isLoading ? (
          <Skeleton className="h-[56px] w-full rounded-[12px]" />
        ) : analyticsQ.data && Object.keys(analyticsQ.data.trends).length > 0 ? (
          <TrendStrip trends={analyticsQ.data.trends} />
        ) : null}

        <Card>
          <CardHeader>
            <CardTitle>Past sessions</CardTitle>
          </CardHeader>
          <CardBody>
            {analyticsQ.isLoading ? (
              <div className="space-y-2" aria-busy>
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : analyticsQ.isError ? (
              <ErrorState
                title="Couldn't load your interview history."
                description="Try again in a moment."
                action={<Button onClick={() => analyticsQ.refetch()}>Retry</Button>}
              />
            ) : !analyticsQ.data || analyticsQ.data.sessions.length === 0 ? (
              <EmptyState
                icon={<MessageSquare className="size-8" strokeWidth={1.5} />}
                title="No sessions yet."
                description="Practice your first visa interview — Pakistan-specific questions for the UK, US, Canada, or Germany."
                action={
                  <Button asChild>
                    <Link href="/interviews/visa">Practice visa</Link>
                  </Button>
                }
              />
            ) : (
              <ul className="divide-y divide-[var(--color-border-quiet)]">
                {analyticsQ.data.sessions.slice(0, 12).map((s) => (
                  <li key={s.session_id} className="py-3">
                    <Link
                      href={`/interviews/${s.session_id}`}
                      className="flex flex-wrap items-center justify-between gap-3"
                    >
                      <div className="min-w-0">
                        <p className="text-[14px] text-ink-deep">
                          {s.practice_mode}
                          <span className="text-ink-muted"> · {s.questions_asked} questions</span>
                        </p>
                        <p className="mt-0.5 font-mono text-[12px] text-ink-subtle">
                          {new Date(s.started_at).toLocaleString()}
                        </p>
                      </div>
                      <Chip tone={s.status === "ended" ? "neutral" : "validated"}>{s.status}</Chip>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      </section>
    </div>
  );
}

export default function InterviewsPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
      <InterviewsInner />
    </Suspense>
  );
}
