"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus, Send, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { endpoints } from "@/lib/api";

type ListField = "strengths" | "revision_priorities" | "caution_notes";

export default function MentorDocumentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const qc = useQueryClient();

  const docQ = useQuery({
    queryKey: ["mentor", "document", id],
    queryFn: () => endpoints.mentors.document(id),
  });

  const [summary, setSummary] = useState("");
  const [strengths, setStrengths] = useState<string[]>([""]);
  const [revisions, setRevisions] = useState<string[]>([""]);
  const [cautions, setCautions] = useState<string[]>([]);

  const submit = useMutation({
    mutationFn: () =>
      endpoints.mentors.submitFeedback(id, {
        summary: summary.trim(),
        strengths: strengths.map((x) => x.trim()).filter(Boolean),
        revision_priorities: revisions.map((x) => x.trim()).filter(Boolean),
        caution_notes: cautions.map((x) => x.trim()).filter(Boolean),
      }),
    onSuccess: () => {
      toast.success("Review submitted.");
      qc.invalidateQueries({ queryKey: ["mentor", "pending"] });
    },
    onError: () => toast.error("Couldn't submit. Try again."),
  });

  const validateForm = () =>
    summary.trim().length > 10 &&
    strengths.some((x) => x.trim()) &&
    revisions.some((x) => x.trim());

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) {
      toast.error("Need a summary plus at least one strength and one revision priority.");
      return;
    }
    submit.mutate();
  };

  const setList = (field: ListField, list: string[]) => {
    if (field === "strengths") setStrengths(list);
    else if (field === "revision_priorities") setRevisions(list);
    else setCautions(list);
  };

  if (docQ.isLoading) {
    return (
      <div className="mx-auto max-w-6xl space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }
  if (docQ.isError || !docQ.data) {
    return (
      <div className="mx-auto max-w-3xl rounded-[20px] border border-[var(--color-border)] bg-paper-white p-10 text-center">
        <h2 className="font-display text-xl text-ink">Document not found.</h2>
        <div className="mt-5">
          <Button asChild>
            <Link href="/mentor/queue">
              <ArrowLeft className="size-4" strokeWidth={2} /> Queue
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  const doc = docQ.data;

  return (
    <div className="mx-auto max-w-7xl space-y-4">
      <Link
        href="/mentor/queue"
        className="inline-flex items-center gap-1 text-sm text-ink-muted hover:text-ink"
      >
        <ArrowLeft className="size-4" strokeWidth={2} /> Queue
      </Link>

      <header>
        <h1 className="font-display text-3xl text-ink">{doc.title}</h1>
        <p className="mt-1 text-ink-muted">
          {doc.document_type} · Submitted {new Date(doc.created_at).toLocaleString()}
        </p>
      </header>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Student draft</CardTitle>
          </CardHeader>
          <CardBody>
            {doc.content_text ? (
              <pre className="max-h-[60vh] overflow-y-auto whitespace-pre-wrap font-sans text-[15px] leading-relaxed text-ink">
                {doc.content_text}
              </pre>
            ) : (
              <p className="text-sm text-ink-subtle">Submitted as a file.</p>
            )}
          </CardBody>
        </Card>

        <form onSubmit={onSubmit} className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Your review</CardTitle>
              <CardDescription>
                Submitted feedback is labeled as reviewed by a human mentor.
              </CardDescription>
            </CardHeader>
            <CardBody className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="summary">Summary</Label>
                <textarea
                  id="summary"
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                  rows={4}
                  placeholder="Overall judgment in 2-4 sentences…"
                  className="w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 py-2 text-[15px] text-ink placeholder:text-ink-subtle focus-visible:border-generated focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
                />
              </div>

              <ListEditor
                label="Strengths"
                placeholder="Concrete strength…"
                items={strengths}
                onChange={(v) => setList("strengths", v)}
                tone="validated"
              />
              <ListEditor
                label="Revision priorities"
                placeholder="Most-impactful revision…"
                items={revisions}
                onChange={(v) => setList("revision_priorities", v)}
                tone="caution"
              />
              <ListEditor
                label="Caution notes (optional)"
                placeholder="Risk to flag…"
                items={cautions}
                onChange={(v) => setList("caution_notes", v)}
                tone="danger"
              />

              <div className="flex items-center justify-end">
                <Button type="submit" loading={submit.isPending} disabled={!validateForm()}>
                  <Send className="size-4" strokeWidth={2} /> Submit review
                </Button>
              </div>
            </CardBody>
          </Card>
        </form>
      </div>
    </div>
  );
}

function ListEditor({
  label,
  placeholder,
  items,
  onChange,
  tone,
}: {
  label: string;
  placeholder: string;
  items: string[];
  onChange: (v: string[]) => void;
  tone: "validated" | "caution" | "danger";
}) {
  const stripeCls =
    tone === "validated"
      ? "validated-stripe"
      : tone === "caution"
        ? "caution-stripe"
        : "border-l-2 border-l-danger pl-3";

  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <ul className="space-y-2">
        {items.map((v, i) => (
          <li key={i} className={`flex items-center gap-2 ${stripeCls}`}>
            <Input
              value={v}
              onChange={(e) => onChange(items.map((x, j) => (i === j ? e.target.value : x)))}
              placeholder={placeholder}
            />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => onChange(items.filter((_, j) => j !== i))}
              aria-label="Remove"
            >
              <Trash2 className="size-4" strokeWidth={2} />
            </Button>
          </li>
        ))}
      </ul>
      <Button type="button" variant="secondary" size="sm" onClick={() => onChange([...items, ""])}>
        <Plus className="size-4" strokeWidth={2} /> Add
      </Button>
    </div>
  );
}
