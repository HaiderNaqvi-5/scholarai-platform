"use client";

/**
 * /documents/professor-email — Elite professor cold-email generator (PRD §0.6).
 *
 * Simple two-panel: structured inputs in, copy-paste-ready email out. Gated to
 * Elite — non-Elite users see <UpgradeWall /> with the currency-correct price
 * from the backend.
 */

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Copy, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { ApiError, endpoints, isPlanRequiredError } from "@/lib/api";
import type {
  PlanRequiredDetail,
  ProfessorEmailRequest,
  ProfessorEmailResponse,
} from "@/lib/api";
import { copyText } from "@/lib/clipboard";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { UpgradeWall } from "@/components/UpgradeWall";

const INITIAL: ProfessorEmailRequest = {
  professor_name: "",
  university: "",
  research_area: "",
  student_pitch: "",
  position_type: "phd",
};

export default function ProfessorEmailPage() {
  const [form, setForm] = useState<ProfessorEmailRequest>(INITIAL);
  const [result, setResult] = useState<ProfessorEmailResponse | null>(null);
  const [wall, setWall] = useState<PlanRequiredDetail | null>(null);

  const generate = useMutation({
    mutationFn: (body: ProfessorEmailRequest) =>
      endpoints.professorEmail.generate(body),
    onSuccess: (response) => {
      setWall(null);
      setResult(response);
      toast.success("Email drafted.");
    },
    onError: (err) => {
      if (isPlanRequiredError(err)) {
        setWall(err.detail);
        return;
      }
      const msg = err instanceof ApiError ? err.message : "Couldn't generate email.";
      toast.error(msg);
    },
  });

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (form.student_pitch.trim().length < 20) {
      toast.error("Add at least 20 characters of background and fit.");
      return;
    }
    generate.mutate(form);
  }

  function set<K extends keyof ProfessorEmailRequest>(key: K, v: ProfessorEmailRequest[K]) {
    setForm((f) => ({ ...f, [key]: v }));
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="mb-5">
        <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">
          Documents · Professor cold-email
        </p>
        <h1 className="mt-1 font-display text-3xl text-ink">
          Email a professor about a PhD or RA position
        </h1>
        <p className="mt-1 max-w-3xl text-ink-muted">
          Specific in two sentences. Anchored to their actual research area. Under
          200 words. Verify everything before sending.
        </p>
      </header>

      {wall ? (
        <UpgradeWall
          detail={wall}
          featureName="Professor cold-email (Elite)"
          showElite
          className="my-6"
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <form onSubmit={onSubmit} className="space-y-4" data-testid="prof-email-form">
            <Card>
              <CardHeader>
                <CardTitle>Inputs</CardTitle>
              </CardHeader>
              <CardBody className="space-y-3">
                <div className="space-y-1.5">
                  <Label htmlFor="pe-name">Professor name</Label>
                  <Input
                    id="pe-name"
                    required
                    value={form.professor_name}
                    onChange={(e) => set("professor_name", e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="pe-uni">University</Label>
                  <Input
                    id="pe-uni"
                    required
                    value={form.university}
                    onChange={(e) => set("university", e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="pe-area">Research area</Label>
                  <Input
                    id="pe-area"
                    required
                    placeholder="machine learning systems for low-resource languages"
                    value={form.research_area}
                    onChange={(e) => set("research_area", e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="pe-pitch">Your background and fit</Label>
                  <textarea
                    id="pe-pitch"
                    rows={5}
                    required
                    value={form.student_pitch}
                    onChange={(e) => set("student_pitch", e.target.value)}
                    className="w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 py-2 text-[15px] text-ink"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="pe-type">Position</Label>
                  <select
                    id="pe-type"
                    value={form.position_type ?? "phd"}
                    onChange={(e) =>
                      set("position_type", e.target.value as "phd" | "ra")
                    }
                    className="h-11 w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 text-[15px] text-ink"
                  >
                    <option value="phd">PhD</option>
                    <option value="ra">Research assistantship</option>
                  </select>
                </div>
                <Button type="submit" loading={generate.isPending}>
                  <Sparkles className="size-4" aria-hidden /> Generate email
                </Button>
              </CardBody>
            </Card>
          </form>

          <div>
            {generate.isPending && (
              <Card>
                <CardBody className="space-y-3">
                  <Skeleton className="h-5 w-40" />
                  <Skeleton className="h-40 w-full" />
                </CardBody>
              </Card>
            )}

            {!generate.isPending && result && <EmailPreview result={result} />}

            {!generate.isPending && !result && (
              <Card className="bg-paper-warm/40">
                <CardBody className="py-10 text-center text-sm text-ink-muted">
                  Fill in the professor&apos;s name, university, and research area,
                  then add a short pitch on why you fit. Hit{" "}
                  <strong>Generate email</strong>.
                </CardBody>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function EmailPreview({ result }: { result: ProfessorEmailResponse }) {
  function copy() {
    const text = `Subject: ${result.email_subject}\n\n${result.email_body}`;
    void copyText(text, "Email copied to clipboard.");
  }
  return (
    <Card className="generated-stripe">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="size-4 text-generated" aria-hidden /> Draft email
        </CardTitle>
        <Button variant="ghost" size="sm" onClick={copy}>
          <Copy className="size-4" aria-hidden /> Copy
        </Button>
      </CardHeader>
      <CardBody className="space-y-3">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-wider text-ink-muted">
            Subject
          </p>
          <p className="mt-1 text-[15px] text-ink">{result.email_subject}</p>
        </div>
        <div>
          <p className="font-mono text-[10px] uppercase tracking-wider text-ink-muted">
            Body
          </p>
          <p className="mt-1 whitespace-pre-line text-[15px] leading-relaxed text-ink">
            {result.email_body}
          </p>
        </div>
        <p className="border-t border-[var(--color-border)] pt-3 text-xs text-ink-muted">
          {result.limitations}
        </p>
      </CardBody>
    </Card>
  );
}
