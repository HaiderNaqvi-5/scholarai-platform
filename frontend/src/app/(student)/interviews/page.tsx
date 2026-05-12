"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, MessageSquare, Plus } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { endpoints } from "@/lib/api";

const MODES = [
  { code: "GENERAL", label: "General prep" },
  { code: "SCHOLARSHIP", label: "Scholarship-specific" },
  { code: "TECHNICAL", label: "Technical" },
];

function InterviewsInner() {
  const router = useRouter();
  const sp = useSearchParams();
  const [mode, setMode] = useState(sp.get("scholarship") ? "SCHOLARSHIP" : "GENERAL");
  const scholarshipId = sp.get("scholarship") ?? undefined;

  const analyticsQ = useQuery({
    queryKey: ["interviews", "analytics"],
    queryFn: endpoints.interviews.analytics,
  });

  const start = useMutation({
    mutationFn: () =>
      endpoints.interviews.start({
        practice_mode: mode,
        scholarship_id: mode === "SCHOLARSHIP" ? scholarshipId : undefined,
      }),
    onSuccess: (s) => router.push(`/interviews/${s.session_id}`),
    onError: () => toast.error("Couldn't start session."),
  });

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <header>
        <h1 className="font-display text-3xl text-ink">Interview practice</h1>
        <p className="mt-1 text-ink-muted">
          One question at a time. Rubric scores update after each answer. Follow-ups target your
          weakest dimension.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Start a session</CardTitle>
          <CardDescription>Pick a practice mode.</CardDescription>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {MODES.map((m) => (
              <button
                key={m.code}
                type="button"
                onClick={() => setMode(m.code)}
                className={`h-10 rounded-full px-4 text-sm transition-colors duration-150 ${
                  mode === m.code
                    ? "bg-ink text-paper"
                    : "border border-[var(--color-border)] bg-paper-white text-ink hover:bg-paper-warm"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
          {mode === "SCHOLARSHIP" && !scholarshipId ? (
            <p className="text-xs text-caution">
              No scholarship selected. Pick one from a scholarship page to scope this practice, or
              switch to General.
            </p>
          ) : null}
          <Button onClick={() => start.mutate()} loading={start.isPending}>
            <Plus className="size-4" strokeWidth={2} /> Start practice
          </Button>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Past sessions</CardTitle>
          <CardDescription>
            {analyticsQ.data
              ? `${analyticsQ.data.sessions.length} session${analyticsQ.data.sessions.length === 1 ? "" : "s"}.`
              : ""}
          </CardDescription>
        </CardHeader>
        <CardBody>
          {analyticsQ.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !analyticsQ.data || analyticsQ.data.sessions.length === 0 ? (
            <p className="text-sm text-ink-subtle">No past sessions yet.</p>
          ) : (
            <ul className="space-y-2">
              {analyticsQ.data.sessions.slice(0, 10).map((s) => (
                <li key={s.session_id}>
                  <Link
                    href={`/interviews/${s.session_id}`}
                    className="flex items-center justify-between gap-3 rounded-[12px] border border-[var(--color-border)] bg-paper-white p-3 hover:border-ink-muted"
                  >
                    <div className="flex items-center gap-3">
                      <MessageSquare className="size-4 text-ink-muted" strokeWidth={2} />
                      <div>
                        <p className="text-sm text-ink">
                          {s.practice_mode}
                          <span className="text-ink-subtle"> · {s.questions_asked} questions</span>
                        </p>
                        <p className="text-xs text-ink-subtle">
                          {new Date(s.started_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge tone={s.status === "ended" ? "neutral" : "validated"}>
                        {s.status}
                      </Badge>
                      <ArrowRight className="size-4 text-ink-subtle" strokeWidth={2} />
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      {analyticsQ.data && analyticsQ.data.recommended_focus.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Recommended focus</CardTitle>
            <CardDescription>Dimensions your past answers scored lowest on.</CardDescription>
          </CardHeader>
          <CardBody>
            <div className="flex flex-wrap gap-2">
              {analyticsQ.data.recommended_focus.map((f) => (
                <Badge key={f} tone="caution">
                  {f}
                </Badge>
              ))}
            </div>
          </CardBody>
        </Card>
      ) : null}
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
