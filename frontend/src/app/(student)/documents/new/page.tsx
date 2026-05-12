"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { FileUp, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { endpoints } from "@/lib/api";

const DOC_TYPES = [
  { code: "SOP", label: "Statement of Purpose" },
  { code: "ESSAY", label: "Personal essay" },
  { code: "RESEARCH_STATEMENT", label: "Research statement" },
  { code: "MOTIVATION_LETTER", label: "Motivation letter" },
];

const DRAFT_KEY = "grantpath.document_draft";

type Draft = {
  title: string;
  document_type: string;
  content_text: string;
  scholarship_ids: string[];
};

function NewDocumentInner() {
  const router = useRouter();
  const sp = useSearchParams();
  const initialScholarship = sp.get("scholarship");

  const [draft, setDraft] = useState<Draft>({
    title: "",
    document_type: "SOP",
    content_text: "",
    scholarship_ids: initialScholarship ? [initialScholarship] : [],
  });
  const [file, setFile] = useState<File | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const savedQ = useQuery({
    queryKey: ["saved"],
    queryFn: endpoints.saved.list,
  });

  useEffect(() => {
    try {
      const raw = localStorage.getItem(DRAFT_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Draft;
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setDraft((d) => ({ ...d, ...parsed }));
      }
    } catch {}
  }, []);

  useEffect(() => {
    const id = setTimeout(() => {
      try {
        localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
        setSavedAt(new Date().toLocaleTimeString());
      } catch {}
    }, 5000);
    return () => clearTimeout(id);
  }, [draft]);

  const update = <K extends keyof Draft>(k: K, v: Draft[K]) =>
    setDraft((d) => ({ ...d, [k]: v }));

  const submit = useMutation({
    mutationFn: () =>
      endpoints.documents.submit({
        document_type: draft.document_type,
        title: draft.title.trim(),
        content_text: draft.content_text || undefined,
        file: file ?? undefined,
        scholarship_ids: draft.scholarship_ids.length > 0 ? draft.scholarship_ids : undefined,
      }),
    onSuccess: (doc) => {
      try {
        localStorage.removeItem(DRAFT_KEY);
      } catch {}
      toast.success("Submitted. Generating feedback.");
      router.replace(`/documents/${doc.id}`);
    },
    onError: () => toast.error("Couldn't submit. Try again."),
  });

  const valid = draft.title.trim().length > 1 && (draft.content_text.length > 50 || file != null);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!valid) {
      toast.error("Add a title and either paste text (50+ chars) or attach a file.");
      return;
    }
    submit.mutate();
  };

  const removeScholarship = (id: string) =>
    update("scholarship_ids", draft.scholarship_ids.filter((x) => x !== id));

  const addScholarship = (id: string) => {
    if (!draft.scholarship_ids.includes(id)) {
      update("scholarship_ids", [...draft.scholarship_ids, id]);
    }
  };

  return (
    <form onSubmit={onSubmit} className="mx-auto max-w-3xl space-y-5">
      <header>
        <h1 className="font-display text-3xl text-ink">New document</h1>
        <p className="mt-1 text-ink-muted">
          Paste your draft or upload a file. Optionally ground feedback against a target scholarship.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Basics</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              value={draft.title}
              onChange={(e) => update("title", e.target.value)}
              placeholder="My SOP for Fulbright 2027"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="doctype">Document type</Label>
            <select
              id="doctype"
              value={draft.document_type}
              onChange={(e) => update("document_type", e.target.value)}
              className="h-11 w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 text-[15px]"
            >
              {DOC_TYPES.map((t) => (
                <option key={t.code} value={t.code}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Content</CardTitle>
          <CardDescription>Paste your draft or attach a file. Either works.</CardDescription>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="content">Paste draft text</Label>
            <textarea
              id="content"
              value={draft.content_text}
              onChange={(e) => update("content_text", e.target.value)}
              rows={12}
              placeholder="Paste your statement here…"
              className="w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 py-2 text-[15px] text-ink placeholder:text-ink-subtle focus-visible:border-generated focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
            />
            <p className="text-xs text-ink-subtle">
              {draft.content_text.length} chars
              {savedAt ? ` · Draft saved at ${savedAt}` : ""}
            </p>
          </div>

          <div className="space-y-2">
            <Label>Or upload a file</Label>
            <div className="flex items-center gap-2">
              <input
                ref={fileRef}
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="hidden"
              />
              <Button
                type="button"
                variant="secondary"
                onClick={() => fileRef.current?.click()}
              >
                <FileUp className="size-4" strokeWidth={2} />
                {file ? "Change file" : "Choose file"}
              </Button>
              {file ? (
                <span className="inline-flex items-center gap-2 text-sm text-ink-muted">
                  {file.name}
                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    aria-label="Remove file"
                    className="text-ink-subtle hover:text-danger"
                  >
                    <X className="size-3.5" strokeWidth={2} />
                  </button>
                </span>
              ) : null}
            </div>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Grounding (optional)</CardTitle>
          <CardDescription>
            Pick scholarships you&apos;re targeting. Feedback cites their published rules.
          </CardDescription>
        </CardHeader>
        <CardBody className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {draft.scholarship_ids.length === 0 ? (
              <p className="text-sm text-ink-subtle">None selected.</p>
            ) : (
              draft.scholarship_ids.map((id) => {
                const s = savedQ.data?.items.find((x) => x.scholarship_id === id);
                return (
                  <Badge key={id} tone="validated" className="gap-1">
                    {s?.scholarship.title ?? id.slice(0, 8)}
                    <button
                      type="button"
                      onClick={() => removeScholarship(id)}
                      aria-label="Remove"
                      className="ml-1 hover:text-danger"
                    >
                      <X className="size-3" strokeWidth={2.5} />
                    </button>
                  </Badge>
                );
              })
            )}
          </div>
          {savedQ.isLoading ? (
            <Skeleton className="h-10 w-full" />
          ) : savedQ.data && savedQ.data.items.length > 0 ? (
            <div className="space-y-2">
              <p className="text-xs uppercase tracking-wider text-ink-subtle">
                From your saved list
              </p>
              <div className="flex flex-wrap gap-2">
                {savedQ.data.items
                  .filter((s) => !draft.scholarship_ids.includes(s.scholarship_id))
                  .slice(0, 8)
                  .map((s) => (
                    <button
                      key={s.scholarship_id}
                      type="button"
                      onClick={() => addScholarship(s.scholarship_id)}
                      className="rounded-full border border-[var(--color-border)] bg-paper-white px-3 py-1 text-xs text-ink hover:bg-paper-warm"
                    >
                      + {s.scholarship.title}
                    </button>
                  ))}
              </div>
            </div>
          ) : null}
        </CardBody>
      </Card>

      <div className="flex items-center justify-end gap-3">
        <Button type="submit" loading={submit.isPending} disabled={!valid}>
          Submit for feedback
        </Button>
      </div>
    </form>
  );
}

export default function NewDocumentPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
      <NewDocumentInner />
    </Suspense>
  );
}
