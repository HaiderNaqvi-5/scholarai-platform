"use client";

/**
 * /interviews/visa — Pakistan visa interview simulator (PRD §8).
 *
 * Setup → question/answer loop with feedback after each answer (study mode) →
 * session summary with rubric radar. Free tier is cut off after Q3; the 402
 * carries a partial_summary that surfaces in <UpgradeWall />.
 */

import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { CheckCircle2, Flag, Lightbulb, RotateCcw, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { ApiError, endpoints, isPlanRequiredError } from "@/lib/api";
import type {
  PlanRequiredDetail,
  VisaCountry,
  VisaInterviewAnswerResponse,
  VisaPracticeMode,
  VisaInterviewQuestion,
  VisaInterviewRubric,
  VisaInterviewStartResponse,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { FeedbackBlock } from "@/components/ui/feedback-block";
import { Badge } from "@/components/ui/badge";
import { RubricRadar } from "@/components/interview/RubricRadar";
import { UpgradeWall } from "@/components/UpgradeWall";
import { cn } from "@/lib/utils";

import { VISA_COUNTRIES } from "@/lib/countries";

const COUNTRIES = VISA_COUNTRIES;

type Phase = "setup" | "running" | "done" | "blocked";

type AnswerRecord = {
  question: VisaInterviewQuestion;
  answerText: string;
  evaluation: VisaInterviewRubric;
};

export default function VisaInterviewPage() {
  const [phase, setPhase] = useState<Phase>("setup");
  const [country, setCountry] = useState<VisaCountry>("GB");
  const [mode, setMode] = useState<VisaPracticeMode>("study");
  const [session, setSession] = useState<VisaInterviewStartResponse | null>(null);
  const [current, setCurrent] = useState<VisaInterviewQuestion | null>(null);
  const [answerText, setAnswerText] = useState("");
  const [history, setHistory] = useState<AnswerRecord[]>([]);
  const [latestEvaluation, setLatestEvaluation] = useState<VisaInterviewRubric | null>(null);
  const [wall, setWall] = useState<PlanRequiredDetail | null>(null);
  const [progress, setProgress] = useState<{ answered: number; total: number }>({ answered: 0, total: 10 });

  const start = useMutation({
    mutationFn: () =>
      endpoints.visaInterview.start({ country, practice_mode: mode }),
    onSuccess: (resp) => {
      setSession(resp);
      setCurrent(resp.first_question ?? null);
      setHistory([]);
      setLatestEvaluation(null);
      setAnswerText("");
      setWall(null);
      setProgress({ answered: 0, total: resp.total_questions });
      setPhase("running");
    },
    onError: (err) => {
      const msg = err instanceof ApiError ? err.message : "Couldn't start session.";
      toast.error(msg);
    },
  });

  const submit = useMutation({
    mutationFn: (text: string) => {
      if (!session || !current) throw new Error("No active question");
      return endpoints.visaInterview.answer(session.session_id, {
        question_id: current.id,
        answer_text: text,
      });
    },
    onSuccess: (resp: VisaInterviewAnswerResponse) => {
      if (!current) return;
      setHistory((h) => [
        ...h,
        { question: current, answerText, evaluation: resp.evaluation },
      ]);
      setLatestEvaluation(resp.evaluation);
      setProgress(resp.session_progress);
      setAnswerText("");
      if (resp.next_question) {
        setCurrent(resp.next_question);
      } else {
        setCurrent(null);
        setPhase("done");
      }
    },
    onError: (err) => {
      if (isPlanRequiredError(err)) {
        setWall(err.detail);
        setPhase("blocked");
        return;
      }
      const msg = err instanceof ApiError ? err.message : "Couldn't submit answer.";
      toast.error(msg);
    },
  });

  function resetAll() {
    setPhase("setup");
    setSession(null);
    setCurrent(null);
    setAnswerText("");
    setHistory([]);
    setLatestEvaluation(null);
    setWall(null);
  }

  return (
    <div className="mx-auto max-w-5xl">
      <header className="mb-5">
        <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">
          Practice · Visa interview
        </p>
        <h1 className="mt-1 font-display text-3xl text-ink">
          Visa interview simulator
        </h1>
        <p className="mt-1 max-w-3xl text-ink-muted">
          Pakistani-context evaluator across clarity, confidence, relevance, and
          red-flag detection. Pick a country and practise mode to begin.
        </p>
      </header>

      {phase === "setup" && (
        <SetupCard
          country={country}
          mode={mode}
          submitting={start.isPending}
          onCountry={setCountry}
          onMode={setMode}
          onStart={() => start.mutate()}
        />
      )}

      {phase === "running" && session && current && (
        <RunningPanel
          session={session}
          question={current}
          mode={mode}
          progress={progress}
          answerText={answerText}
          setAnswerText={setAnswerText}
          submitting={submit.isPending}
          onSubmit={() => submit.mutate(answerText)}
          latestEvaluation={latestEvaluation}
          totalAnswered={history.length}
          onReset={resetAll}
        />
      )}

      {phase === "blocked" && wall && (
        <UpgradeWall detail={wall} featureName="Visa interview (Q4–Q10)" showElite />
      )}

      {phase === "done" && session && (
        <SummaryPanel sessionId={session.session_id} onReset={resetAll} history={history} />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

function SetupCard({
  country,
  mode,
  submitting,
  onCountry,
  onMode,
  onStart,
}: {
  country: VisaCountry;
  mode: VisaPracticeMode;
  submitting: boolean;
  onCountry: (c: VisaCountry) => void;
  onMode: (m: VisaPracticeMode) => void;
  onStart: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Set up your session</CardTitle>
      </CardHeader>
      <CardBody className="space-y-5">
        <div>
          <Label className="mb-2 block">Target country</Label>
          <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
            {COUNTRIES.map((c) => (
              <button
                key={c.code}
                type="button"
                onClick={() => onCountry(c.code)}
                aria-pressed={country === c.code}
                className={cn(
                  "rounded-[14px] border bg-paper-white px-3 py-3 text-left transition-colors",
                  country === c.code
                    ? "border-ink ring-2 ring-[var(--color-ring)]"
                    : "border-[var(--color-border)] hover:bg-paper-warm",
                )}
              >
                <p className="font-display text-xl text-ink">{c.code}</p>
                <p className="mt-1 text-sm text-ink">{c.label}</p>
              </button>
            ))}
          </div>
        </div>

        <div>
          <Label className="mb-2 block">Practice mode</Label>
          <div className="grid grid-cols-2 gap-2">
            <ModeOption
              active={mode === "study"}
              onClick={() => onMode("study")}
              title="Study mode"
              hint="See feedback after every answer."
            />
            <ModeOption
              active={mode === "exam"}
              onClick={() => onMode("exam")}
              title="Exam mode"
              hint="No hints — review at the end."
            />
          </div>
        </div>

        <Button onClick={onStart} loading={submitting}>
          Start practice session
        </Button>
      </CardBody>
    </Card>
  );
}

function ModeOption({
  active,
  onClick,
  title,
  hint,
}: {
  active: boolean;
  onClick: () => void;
  title: string;
  hint: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "rounded-[14px] border bg-paper-white p-3 text-left transition-colors",
        active
          ? "border-ink ring-2 ring-[var(--color-ring)]"
          : "border-[var(--color-border)] hover:bg-paper-warm",
      )}
    >
      <p className="text-sm font-medium text-ink">{title}</p>
      <p className="mt-1 text-xs text-ink-muted">{hint}</p>
    </button>
  );
}

// ---------------------------------------------------------------------------
// Running
// ---------------------------------------------------------------------------

function RunningPanel({
  session,
  question,
  mode,
  progress,
  answerText,
  setAnswerText,
  submitting,
  onSubmit,
  latestEvaluation,
  totalAnswered,
  onReset,
}: {
  session: VisaInterviewStartResponse;
  question: VisaInterviewQuestion;
  mode: VisaPracticeMode;
  progress: { answered: number; total: number };
  answerText: string;
  setAnswerText: (v: string) => void;
  submitting: boolean;
  onSubmit: () => void;
  latestEvaluation: VisaInterviewRubric | null;
  totalAnswered: number;
  onReset: () => void;
}) {
  const pct = progress.total > 0 ? Math.round((progress.answered / progress.total) * 100) : 0;

  return (
    <div className="space-y-4">
      <Card>
        <CardBody>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="font-mono text-xs uppercase tracking-wide text-ink-muted">
              {session.country} · {session.visa_type} · {mode}
            </p>
            <Button variant="ghost" size="sm" onClick={onReset}>
              <RotateCcw className="size-4" aria-hidden /> Start over
            </Button>
          </div>
          <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-paper-warm">
            <div
              className="h-full bg-validated transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="mt-1 text-xs text-ink-muted">
            Question {Math.min(progress.answered + 1, progress.total)} of {progress.total}
          </p>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <Badge tone="neutral">{question.category}</Badge>
          <CardTitle className="mt-2">{question.question_text}</CardTitle>
        </CardHeader>
        <CardBody className="space-y-3">
          <textarea
            value={answerText}
            onChange={(e) => setAnswerText(e.target.value)}
            rows={6}
            placeholder="Type your answer the way you would speak it…"
            className="w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 py-2 text-[15px] text-ink"
          />
          <Button
            onClick={onSubmit}
            loading={submitting}
            disabled={!answerText.trim()}
          >
            Submit answer
          </Button>
        </CardBody>
      </Card>

      {mode === "study" && latestEvaluation && totalAnswered > 0 && (
        <FeedbackPanel rubric={latestEvaluation} />
      )}
    </div>
  );
}

function FeedbackPanel({ rubric }: { rubric: VisaInterviewRubric }) {
  return (
    <Card className="generated-stripe">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="size-4 text-generated" aria-hidden /> Feedback
        </CardTitle>
        <p className="mt-1 text-xs text-ink-muted">
          Scores are 0–10. Visa officers reward clarity and credible intent.
        </p>
      </CardHeader>
      <CardBody className="space-y-4">
        <div className="grid grid-cols-3 gap-3">
          <Meter label="Clarity" value={rubric.clarity_score} />
          <Meter label="Confidence" value={rubric.confidence_score} />
          <Meter label="Relevance" value={rubric.relevance_score} />
        </div>

        {rubric.red_flags.length > 0 && (
          <FeedbackBlock tone="danger" icon={<Flag className="size-4" />} title="Red flags">
            <ul className="list-disc space-y-1 pl-4">
              {rubric.red_flags.map((rf, i) => (
                <li key={i}>{rf}</li>
              ))}
            </ul>
          </FeedbackBlock>
        )}

        <FeedbackBlock
          tone="ok"
          icon={<CheckCircle2 className="size-4" />}
          title="What was good"
        >
          {rubric.what_was_good}
        </FeedbackBlock>

        {rubric.missing_elements.length > 0 && (
          <FeedbackBlock
            tone="warn"
            icon={<Lightbulb className="size-4" />}
            title="What to add"
          >
            <ul className="list-disc space-y-1 pl-4">
              {rubric.missing_elements.map((m, i) => (
                <li key={i}>{m}</li>
              ))}
            </ul>
          </FeedbackBlock>
        )}

        <FeedbackBlock tone="ink" title="Ideal answer includes">
          {rubric.ideal_answer_summary}
        </FeedbackBlock>
      </CardBody>
    </Card>
  );
}

function Meter({ label, value }: { label: string; value: number }) {
  const pct = Math.max(0, Math.min(10, value)) * 10;
  return (
    <div className="rounded-[12px] bg-paper-warm p-3">
      <p className="font-mono text-[10px] uppercase tracking-wide text-ink-muted">
        {label}
      </p>
      <p className="mt-1 font-display text-2xl text-ink">{value}/10</p>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-paper-dim">
        <div className="h-full bg-validated" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}


// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------

function SummaryPanel({
  sessionId,
  onReset,
  history,
}: {
  sessionId: string;
  onReset: () => void;
  history: AnswerRecord[];
}) {
  const summaryQ = useQuery({
    queryKey: ["visa-interview", sessionId, "summary"],
    queryFn: () => endpoints.visaInterview.summary(sessionId),
  });

  const radarDims = useMemo(() => {
    if (!summaryQ.data) return [];
    return Object.entries(summaryQ.data.score_breakdown).map(([k, v]) => ({
      dimension: k,
      score: v,
    }));
  }, [summaryQ.data]);

  if (summaryQ.isLoading) {
    return <Skeleton className="h-96 w-full" />;
  }
  if (!summaryQ.data) {
    return (
      <Card>
        <CardBody className="space-y-3 text-center">
          <p className="text-ink">Couldn&apos;t load summary.</p>
          <Button onClick={() => summaryQ.refetch()}>Retry</Button>
        </CardBody>
      </Card>
    );
  }
  const s = summaryQ.data;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Session summary</CardTitle>
          <p className="mt-1 text-sm text-ink-muted">
            {s.country} · {s.visa_type} · {s.answered}/{s.total} answered ·
            average {s.average_score.toFixed(1)}/10 ·{" "}
            {s.red_flag_count === 0 ? "no red flags" : `${s.red_flag_count} red flag(s)`}
          </p>
        </CardHeader>
        <CardBody>
          <RubricRadar dimensions={radarDims} scale="0-10" />
        </CardBody>
      </Card>

      {s.areas_to_improve.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Areas to improve</CardTitle>
          </CardHeader>
          <CardBody>
            <ul className="list-disc space-y-1 pl-5 text-sm text-ink">
              {s.areas_to_improve.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </CardBody>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Question-by-question</CardTitle>
        </CardHeader>
        <CardBody className="space-y-3">
          {history.map((row, i) => (
            <div
              key={i}
              className="rounded-[12px] border border-[var(--color-border)] p-3"
            >
              <p className="font-mono text-[10px] uppercase tracking-wide text-ink-muted">
                Q{i + 1} · {row.question.category}
              </p>
              <p className="mt-1 text-sm font-medium text-ink">
                {row.question.question_text}
              </p>
              <p className="mt-2 text-xs text-ink-muted">
                Clarity {row.evaluation.clarity_score} · Confidence{" "}
                {row.evaluation.confidence_score} · Relevance{" "}
                {row.evaluation.relevance_score} · Overall{" "}
                {row.evaluation.overall_score}
              </p>
            </div>
          ))}
        </CardBody>
      </Card>

      <div className="flex items-center justify-end gap-2">
        <Button variant="secondary" onClick={onReset}>
          Practise again
        </Button>
      </div>
    </div>
  );
}
