"use client";

/**
 * /documents/sop — Pakistan-context SOP builder (PRD §7).
 *
 * Two-panel: structured input form on the left, generated draft on the right
 * with paragraph labels, copy/download/regenerate, and an Elite-only
 * line-by-line feedback side panel. Free tier is capped at 1 lifetime SOP —
 * the 402 surfaces as <UpgradeWall /> with the backend's currency-correct
 * price message.
 */

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Copy, Download, Mail, RotateCcw, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { ApiError, endpoints, isPlanRequiredError } from "@/lib/api";
import { copyText, downloadText } from "@/lib/clipboard";
import type {
  PlanRequiredDetail,
  SOPDraftRequest,
  SOPDraftResponse,
  SOPInputs,
} from "@/lib/api";
import { useAuth } from "@/lib/auth/AuthProvider";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { FeedbackBlock } from "@/components/ui/feedback-block";
import { UpgradeWall } from "@/components/UpgradeWall";
import Link from "next/link";

const INITIAL_INPUTS: SOPInputs = {
  academic_background: "",
  research_experience: null,
  professional_experience: null,
  why_this_program: "",
  why_this_country: null,
  career_goals: "",
  challenges_overcome: null,
  gap_explanation: null,
};

export default function SOPPage() {
  const auth = useAuth();
  const isElite =
    auth.status === "authed" &&
    (auth.user.plan === "elite" || auth.user.plan === "institution");

  const [inputs, setInputs] = useState<SOPInputs>(INITIAL_INPUTS);
  const [programName, setProgramName] = useState("");
  const [draft, setDraft] = useState<SOPDraftResponse | null>(null);
  const [wall, setWall] = useState<PlanRequiredDetail | null>(null);

  const generate = useMutation({
    mutationFn: (body: SOPDraftRequest) => endpoints.sopBuilder.draft(body),
    onSuccess: (response) => {
      setWall(null);
      setDraft(response);
      toast.success("Draft generated.");
    },
    onError: (err) => {
      if (isPlanRequiredError(err)) {
        setWall(err.detail);
        return;
      }
      const msg = err instanceof ApiError ? err.message : "Couldn't generate draft.";
      toast.error(msg);
    },
  });

  function runGenerate() {
    if (inputs.academic_background.trim().length < 20) {
      toast.error("Add at least 20 characters of academic background.");
      return;
    }
    generate.mutate({
      program_name: programName || null,
      sop_inputs: inputs,
    });
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    runGenerate();
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="mb-5">
        <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">
          Documents · SOP builder
        </p>
        <h1 className="mt-1 font-display text-3xl text-ink">
          Statement of Purpose
        </h1>
        <p className="mt-1 max-w-3xl text-ink-muted">
          Structured Pakistan-context inputs in. Six-paragraph draft out.
          Personalise the result — admissions readers spot generic AI prose.
        </p>
        <p className="mt-2 text-xs text-ink-muted">
          Also try the{" "}
          <Link href="/documents/professor-email" className="underline">
            professor cold-email generator
          </Link>{" "}
          (Elite).
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_1.25fr]">
        <SOPForm
          programName={programName}
          setProgramName={setProgramName}
          inputs={inputs}
          setInputs={setInputs}
          submitting={generate.isPending}
          onSubmit={onSubmit}
        />

        <div className="space-y-4">
          {wall ? (
            <UpgradeWall
              detail={wall}
              featureName="SOP builder"
              showElite
            />
          ) : null}

          {!wall && generate.isPending && (
            <Card>
              <CardBody className="space-y-3">
                <Skeleton className="h-5 w-40" />
                <Skeleton className="h-32 w-full" />
                <Skeleton className="h-32 w-full" />
              </CardBody>
            </Card>
          )}

          {!wall && !generate.isPending && draft && (
            <DraftPreview draft={draft} onRegenerate={runGenerate} />
          )}

          {!wall && !generate.isPending && !draft && (
            <Card className="bg-paper-warm/40">
              <CardBody className="py-10 text-center text-sm text-ink-muted">
                Fill in your background and click <strong>Generate draft</strong>.
                {!isElite && (
                  <p className="mt-2 text-xs">
                    Free accounts get one lifetime SOP. Upgrade to Pro for
                    unlimited drafts and Elite for line-by-line feedback.
                  </p>
                )}
              </CardBody>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Form
// ---------------------------------------------------------------------------

function SOPForm({
  programName,
  setProgramName,
  inputs,
  setInputs,
  submitting,
  onSubmit,
}: {
  programName: string;
  setProgramName: (v: string) => void;
  inputs: SOPInputs;
  setInputs: (i: SOPInputs) => void;
  submitting: boolean;
  onSubmit: (e: React.FormEvent) => void;
}) {
  // Single ref-stable change handler. Returning fresh `{ onChange }` objects
  // per render per field broke React's identity-based render skipping; this
  // closure captures only the current `inputs` reference.
  const handleChange = (
    key: keyof SOPInputs,
    opts: { nullable?: boolean } = {},
  ) => (e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
    const v = e.target.value;
    setInputs({ ...inputs, [key]: opts.nullable && v === "" ? null : v });
  };
  const valueOf = (key: keyof SOPInputs): string => (inputs[key] ?? "") as string;
  function bind<K extends keyof SOPInputs>(key: K, opts?: { nullable?: boolean }) {
    return { value: valueOf(key), onChange: handleChange(key, opts) };
  }

  return (
    <form onSubmit={onSubmit} className="space-y-5" data-testid="sop-form">
      <Card>
        <CardHeader>
          <CardTitle>Step 1 — Target program</CardTitle>
        </CardHeader>
        <CardBody className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="sop-program">Program name</Label>
            <Input
              id="sop-program"
              placeholder="MS Computer Science"
              value={programName}
              onChange={(e) => setProgramName(e.target.value)}
            />
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Step 2 — Academic background</CardTitle>
        </CardHeader>
        <CardBody className="space-y-3">
          <Field
            id="sop-academic"
            label="Academic background"
            hint="Where you studied, CGPA, project highlights. 20+ chars."
            required
            textarea
            rows={4}
            {...bind("academic_background")}
          />
          <Field
            id="sop-research"
            label="Research experience (optional)"
            textarea
            rows={3}
            {...bind("research_experience", { nullable: true })}
          />
          <Field
            id="sop-pro"
            label="Professional experience (optional)"
            textarea
            rows={3}
            {...bind("professional_experience", { nullable: true })}
          />
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Step 3 — Motivation</CardTitle>
        </CardHeader>
        <CardBody className="space-y-3">
          <Field
            id="sop-why-program"
            label="Why this specific program"
            required
            textarea
            rows={4}
            {...bind("why_this_program")}
          />
          <Field
            id="sop-why-country"
            label="Why this country (optional)"
            textarea
            rows={3}
            {...bind("why_this_country", { nullable: true })}
          />
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Step 4 — Goals & Pakistan context</CardTitle>
        </CardHeader>
        <CardBody className="space-y-3">
          <Field
            id="sop-goals"
            label="Career goals"
            required
            textarea
            rows={3}
            {...bind("career_goals")}
          />
          <Field
            id="sop-challenges"
            label="Challenges overcome (optional)"
            textarea
            rows={3}
            {...bind("challenges_overcome", { nullable: true })}
          />
          <Field
            id="sop-gap"
            label="Gap explanation (optional)"
            textarea
            rows={2}
            {...bind("gap_explanation", { nullable: true })}
          />
        </CardBody>
      </Card>

      <div className="flex items-center gap-2">
        <Button type="submit" loading={submitting}>
          <Sparkles className="size-4" aria-hidden /> Generate draft
        </Button>
      </div>
    </form>
  );
}

function Field({
  id,
  label,
  hint,
  required,
  textarea,
  rows,
  value,
  onChange,
}: {
  id: string;
  label: string;
  hint?: string;
  required?: boolean;
  textarea?: boolean;
  rows?: number;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => void;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>
        {label}
        {required && <span className="ml-1 text-danger">*</span>}
      </Label>
      {textarea ? (
        <textarea
          id={id}
          rows={rows ?? 3}
          required={required}
          value={value}
          onChange={onChange}
          className="w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 py-2 text-[15px] text-ink"
        />
      ) : (
        <Input id={id} value={value} onChange={onChange} required={required} />
      )}
      {hint && <p className="text-xs text-ink-muted">{hint}</p>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Preview
// ---------------------------------------------------------------------------

function DraftPreview({
  draft,
  onRegenerate,
}: {
  draft: SOPDraftResponse;
  onRegenerate: () => void;
}) {
  const paragraphs = draft.draft_content
    .split("\n\n")
    .map((p) => p.trim())
    .filter(Boolean);

  const copy = () => copyText(draft.draft_content, "Copied draft to clipboard.");
  const download = () => downloadText("sop-draft.txt", draft.draft_content);

  return (
    <div className="space-y-4">
      <Card className="generated-stripe">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="size-4 text-generated" aria-hidden /> SOP draft
            </CardTitle>
            <p className="mt-1 text-xs text-ink-muted">
              {draft.word_count} words · {draft.model_used}
              {draft.used_llm ? "" : " (offline fallback)"}
            </p>
          </div>
          <div className="flex gap-1">
            <Button variant="ghost" size="sm" onClick={copy}>
              <Copy className="size-4" aria-hidden /> Copy
            </Button>
            <Button variant="ghost" size="sm" onClick={download}>
              <Download className="size-4" aria-hidden /> .txt
            </Button>
            <Button variant="secondary" size="sm" onClick={onRegenerate}>
              <RotateCcw className="size-4" aria-hidden /> Regenerate
            </Button>
          </div>
        </CardHeader>
        <CardBody className="space-y-4">
          {paragraphs.map((p, idx) => (
            <section key={idx}>
              <p className="font-mono text-[10px] uppercase tracking-wider text-ink-muted">
                {draft.paragraph_labels[idx] ?? `Section ${idx + 1}`}
              </p>
              <p className="mt-1 whitespace-pre-line text-[15px] leading-relaxed text-ink">
                {p}
              </p>
            </section>
          ))}
          <p className="border-t border-[var(--color-border)] pt-3 text-xs text-ink-muted">
            {draft.grounded_context.limitations}
          </p>
        </CardBody>
      </Card>

      {draft.line_feedback && draft.line_feedback.length > 0 ? (
        <LineFeedback feedback={draft.line_feedback} />
      ) : (
        <EliteUpsell />
      )}
    </div>
  );
}

function LineFeedback({
  feedback,
}: {
  feedback: NonNullable<SOPDraftResponse["line_feedback"]>;
}) {
  return (
    <Card className="generated-stripe">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="size-4 text-generated" aria-hidden /> Line-by-line
          feedback
        </CardTitle>
        <p className="mt-1 text-xs text-ink-muted">
          Elite review — strength, weakness, suggested rewrite per paragraph.
        </p>
      </CardHeader>
      <CardBody className="space-y-3">
        {feedback.map((row) => (
          <details
            key={row.index}
            className="rounded-[12px] border border-[var(--color-border)] bg-paper-white p-3"
          >
            <summary className="cursor-pointer text-sm font-medium text-ink">
              §{row.index} · {row.paragraph_label}
            </summary>
            <dl className="mt-2 space-y-2 text-sm">
              <FeedbackBlock tone="ok" title="What works">{row.strength}</FeedbackBlock>
              <FeedbackBlock tone="warn" title="Where it&apos;s generic">{row.weakness}</FeedbackBlock>
              <FeedbackBlock tone="ink" title="Suggested rewrite">{row.suggestion}</FeedbackBlock>
            </dl>
          </details>
        ))}
      </CardBody>
    </Card>
  );
}


function EliteUpsell() {
  return (
    <Card className="bg-paper-warm/40">
      <CardBody className="flex items-center justify-between gap-3">
        <div>
          <p className="font-display text-sm text-ink">
            Want line-by-line AI feedback on every paragraph?
          </p>
          <p className="mt-1 text-xs text-ink-muted">
            Elite reviews each paragraph for clichés and adds a suggested
            rewrite. Pro stays unlimited drafts.
          </p>
        </div>
        <Button asChild variant="secondary">
          <Link href="/upgrade?plan=elite">
            <Mail className="size-4" aria-hidden /> Compare plans
          </Link>
        </Button>
      </CardBody>
    </Card>
  );
}
