"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check, EyeOff, Send, X } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { endpoints } from "@/lib/api";
import type { CurationRecord } from "@/lib/api";

const TONE: Record<string, "neutral" | "validated" | "caution"> = {
  raw: "caution",
  validated: "neutral",
  published: "validated",
};

export default function CurationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const qc = useQueryClient();
  const [note, setNote] = useState("");

  const recordQ = useQuery({
    queryKey: ["curation", "record", id],
    queryFn: () => endpoints.curation.recordDetail(id),
  });

  const onSuccess = (data: CurationRecord, label: string) => {
    qc.setQueryData(["curation", "record", id], data);
    qc.invalidateQueries({ queryKey: ["curation", "records"] });
    toast.success(`${label} successful.`);
    setNote("");
  };

  const approve = useMutation({
    mutationFn: () => endpoints.curation.approve(id, note || undefined),
    onSuccess: (data) => onSuccess(data, "Approve"),
    onError: () => toast.error("Approve failed."),
  });
  const reject = useMutation({
    mutationFn: () => endpoints.curation.reject(id, note),
    onSuccess: (data) => onSuccess(data, "Reject"),
    onError: () => toast.error("Reject failed."),
  });
  const publish = useMutation({
    mutationFn: () => endpoints.curation.publish(id, note || undefined),
    onSuccess: (data) => onSuccess(data, "Publish"),
    onError: () => toast.error("Publish failed."),
  });
  const unpublish = useMutation({
    mutationFn: () => endpoints.curation.unpublish(id, note || undefined),
    onSuccess: (data) => onSuccess(data, "Unpublish"),
    onError: () => toast.error("Unpublish failed."),
  });

  if (recordQ.isLoading) {
    return (
      <div className="mx-auto max-w-4xl space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  if (recordQ.isError || !recordQ.data) {
    return (
      <div className="mx-auto max-w-3xl rounded-[20px] border border-[var(--color-border)] bg-paper-white p-10 text-center">
        <h2 className="font-display text-xl text-ink">Record not found.</h2>
      </div>
    );
  }

  const r = recordQ.data;
  const canApprove = r.record_state === "raw";
  const canReject = r.record_state === "raw";
  const canPublish = r.record_state === "validated";
  const canUnpublish = r.record_state === "published";

  // Backend CurationRecordDetail has no `fields` blob — assemble the editable
  // facts from the typed columns for the read-only viewer.
  const fields = {
    provider_name: r.provider_name,
    country_code: r.country_code,
    summary: r.summary,
    funding_summary: r.funding_summary,
    field_tags: r.field_tags,
    degree_levels: r.degree_levels,
    citizenship_rules: r.citizenship_rules,
    min_gpa_value: r.min_gpa_value,
    source_url: r.source_url,
    source_document_ref: r.source_document_ref,
  };

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <Link
        href="/admin/curation"
        className="inline-flex items-center gap-1 text-sm text-ink-muted hover:text-ink"
      >
        <ArrowLeft className="size-4" strokeWidth={2} /> Curation
      </Link>

      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-display text-[24px] italic font-[450] leading-[1.2] tracking-[-0.02em] text-ink-deep">
            {r.title}
          </h1>
          <p className="mt-1 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
            {r.record_id}
          </p>
        </div>
        <Badge tone={TONE[r.record_state] ?? "neutral"}>{r.record_state}</Badge>
      </header>

      {r.review_notes ? (
        <div className="rounded-[12px] border border-danger/40 bg-danger-soft px-4 py-2 text-sm text-danger">
          <strong>Review notes:</strong> {r.review_notes}
        </div>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Fields</CardTitle>
        </CardHeader>
        <CardBody>
          <pre className="max-h-96 overflow-auto rounded-[8px] bg-paper-warm/40 p-3 font-mono text-xs text-ink">
            {JSON.stringify(fields, null, 2)}
          </pre>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Actions</CardTitle>
          <CardDescription>
            Reject requires a note. Approve/publish/unpublish notes are optional but recommended.
          </CardDescription>
        </CardHeader>
        <CardBody className="space-y-3">
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={3}
            placeholder="Audit note…"
            className="w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 py-2 text-[15px] text-ink placeholder:text-ink-subtle focus-visible:border-generated focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
          />
          <div className="flex flex-wrap gap-2">
            <Button
              variant="validated"
              onClick={() => approve.mutate()}
              loading={approve.isPending}
              disabled={!canApprove}
            >
              <Check className="size-4" strokeWidth={2} /> Approve
            </Button>
            <Button
              variant="danger"
              onClick={() => {
                if (!note.trim()) {
                  toast.error("Reject needs a note.");
                  return;
                }
                reject.mutate();
              }}
              loading={reject.isPending}
              disabled={!canReject}
            >
              <X className="size-4" strokeWidth={2} /> Reject
            </Button>
            <Button
              onClick={() => publish.mutate()}
              loading={publish.isPending}
              disabled={!canPublish}
            >
              <Send className="size-4" strokeWidth={2} /> Publish
            </Button>
            <Button
              variant="secondary"
              onClick={() => unpublish.mutate()}
              loading={unpublish.isPending}
              disabled={!canUnpublish}
            >
              <EyeOff className="size-4" strokeWidth={2} /> Unpublish
            </Button>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
