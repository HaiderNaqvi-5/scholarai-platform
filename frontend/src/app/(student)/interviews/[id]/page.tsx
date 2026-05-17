"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Send, TrendingDown, TrendingUp, Minus } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { endpoints } from "@/lib/api";
import type { InterviewRubricDimension } from "@/lib/api";
import { RubricRadar } from "@/components/interview/RubricRadar";

export default function InterviewSessionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const qc = useQueryClient();
  const [answer, setAnswer] = useState("");

  const sessionQ = useQuery({
    queryKey: ["interview", id],
    queryFn: () => endpoints.interviews.detail(id),
  });

  const questionQ = useQuery({
    queryKey: ["interview", id, "question"],
    queryFn: () => endpoints.interviews.question(id),
    enabled: sessionQ.data?.status === "active",
  });

  const submit = useMutation({
    mutationFn: (text_response: string) => endpoints.interviews.answer(id, text_response),
    onSuccess: (data) => {
      qc.setQueryData(["interview", id], data);
      qc.invalidateQueries({ queryKey: ["interview", id, "question"] });
      qc.invalidateQueries({ queryKey: ["interviews", "analytics"] });
      setAnswer("");
      toast.success("Answer recorded.");
    },
    onError: () => toast.error("Couldn't submit answer."),
  });

  if (sessionQ.isLoading) {
    return (
      <div className="mx-auto max-w-4xl space-y-4">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (sessionQ.isError || !sessionQ.data) {
    return (
      <div className="mx-auto max-w-3xl rounded-[20px] border border-[var(--color-border)] bg-paper-white p-10 text-center">
        <h2 className="font-display text-xl text-ink">Session not found.</h2>
        <div className="mt-5">
          <Button asChild>
            <Link href="/interviews">
              <ArrowLeft className="size-4" strokeWidth={2} /> Back
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  const session = sessionQ.data;
  const ended = session.status === "ended";
  const weakest =
    session.rubric_scores.length > 0
      ? [...session.rubric_scores].sort((a, b) => a.score - b.score)[0]
      : null;

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (answer.trim().length < 10) {
      toast.error("Write at least a couple sentences.");
      return;
    }
    submit.mutate(answer.trim());
  };

  return (
    <div className="mx-auto max-w-5xl space-y-5" data-testid="interview-session-shell">
      <Link
        href="/interviews"
        className="inline-flex items-center gap-1 text-sm text-ink-muted hover:text-ink"
      >
        <ArrowLeft className="size-4" strokeWidth={2} /> Interviews
      </Link>

      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl text-ink">{session.practice_mode} practice</h1>
          <p className="mt-1 text-ink-muted">
            {session.questions_asked} answered · Started{" "}
            {new Date(session.started_at).toLocaleString()}
          </p>
        </div>
        <Badge tone={ended ? "neutral" : "validated"}>{session.status}</Badge>
      </header>

      <div className="grid gap-5 lg:grid-cols-[1fr_360px]">
        <div className="space-y-4">
          {ended ? (
            <Card>
              <CardHeader>
                <CardTitle>Session complete</CardTitle>
                <CardDescription>
                  Ended {session.ended_at ? new Date(session.ended_at).toLocaleString() : "—"}.
                </CardDescription>
              </CardHeader>
              <CardBody>
                <Button asChild>
                  <Link href="/interviews">Back to interviews</Link>
                </Button>
              </CardBody>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>
                  Question {(questionQ.data?.question_index ?? session.questions_asked) + 1}
                </CardTitle>
                {weakest ? (
                  <CardDescription>
                    Targeting your weakest dimension: <strong>{weakest.dimension}</strong>
                  </CardDescription>
                ) : null}
              </CardHeader>
              <CardBody className="space-y-4">
                {questionQ.isLoading ? (
                  <Skeleton className="h-16 w-full" />
                ) : questionQ.isError ? (
                  <p className="text-sm text-danger">Couldn&apos;t load next question.</p>
                ) : questionQ.data ? (
                  <>
                    <p className="font-display text-lg text-ink">{questionQ.data.question_text}</p>
                    {questionQ.data.guidance_hint ? (
                      <p className="text-xs text-ink-subtle">{questionQ.data.guidance_hint}</p>
                    ) : null}
                    <Badge tone="neutral">{questionQ.data.dimension_focus}</Badge>
                  </>
                ) : null}

                <form onSubmit={onSubmit} className="space-y-3">
                  <textarea
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    rows={8}
                    placeholder="Write your answer here…"
                    className="w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 py-2 text-[15px] text-ink placeholder:text-ink-subtle focus-visible:border-generated focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
                  />
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs text-ink-subtle">{answer.length} chars</span>
                    <Button type="submit" loading={submit.isPending} disabled={answer.trim().length < 10}>
                      <Send className="size-4" strokeWidth={2} /> Submit answer
                    </Button>
                  </div>
                </form>
              </CardBody>
            </Card>
          )}
        </div>

        <aside className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Rubric</CardTitle>
              <CardDescription>0-5 per dimension. Updates after each answer.</CardDescription>
            </CardHeader>
            <CardBody>
              <RubricRadar dimensions={session.rubric_scores} />
              <ul className="mt-3 space-y-1.5">
                {session.rubric_scores.map((d) => (
                  <RubricRow key={d.dimension} d={d} />
                ))}
              </ul>
            </CardBody>
          </Card>
        </aside>
      </div>
    </div>
  );
}

function RubricRow({ d }: { d: InterviewRubricDimension }) {
  const trendIcon =
    d.trend === "up" ? (
      <TrendingUp className="size-3.5 text-validated" strokeWidth={2} />
    ) : d.trend === "down" ? (
      <TrendingDown className="size-3.5 text-danger" strokeWidth={2} />
    ) : (
      <Minus className="size-3.5 text-ink-subtle" strokeWidth={2} />
    );
  return (
    <li className="flex items-center justify-between text-sm">
      <span className="text-ink">{d.dimension}</span>
      <span className="flex items-center gap-1 font-mono text-ink">
        {d.score.toFixed(1)} {trendIcon}
      </span>
    </li>
  );
}
