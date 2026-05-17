"use client";

import { use } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowLeft,
  BookText,
  ExternalLink,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { endpoints } from "@/lib/api";
import type { DocumentDetail, DocumentFeedbackPartition } from "@/lib/api";

export default function DocumentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const qc = useQueryClient();

  const docQ = useQuery({
    queryKey: ["document", id],
    queryFn: () => endpoints.documents.detail(id),
    refetchInterval: (q) => {
      const status = q.state.data?.processing_status;
      return status === "pending" || status === "processing" ? 3000 : false;
    },
  });

  const refresh = useMutation({
    mutationFn: () => endpoints.documents.refreshFeedback(id),
    onSuccess: (data) => {
      qc.setQueryData(["document", id], data);
      toast.success("Feedback refreshed.");
    },
    onError: () => toast.error("Couldn't refresh feedback."),
  });

  if (docQ.isLoading) {
    return (
      <div className="mx-auto max-w-4xl space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (docQ.isError || !docQ.data) {
    return (
      <div className="mx-auto max-w-3xl rounded-[20px] border border-[var(--color-border)] bg-paper-white p-10 text-center">
        <h2 className="font-display text-xl text-ink">Document not found.</h2>
        <div className="mt-5">
          <Button asChild>
            <Link href="/documents">
              <ArrowLeft className="size-4" strokeWidth={2} /> Back to documents
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  const doc = docQ.data;
  const fb = doc.latest_feedback;

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <Link
        href="/documents"
        className="inline-flex items-center gap-1 text-sm text-ink-muted hover:text-ink"
      >
        <ArrowLeft className="size-4" strokeWidth={2} /> Documents
      </Link>

      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-display text-[24px] italic font-[450] leading-[1.2] tracking-[-0.02em] text-ink-deep">
            {doc.title}
          </h1>
          <p className="mt-1 font-mono text-[12px] text-ink-muted">
            {doc.document_type} · Updated {new Date(doc.updated_at ?? doc.created_at).toLocaleString()}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge doc={doc} />
          <Button
            variant="secondary"
            onClick={() => refresh.mutate()}
            loading={refresh.isPending}
          >
            <RefreshCw className="size-4" strokeWidth={2} /> Re-run
          </Button>
        </div>
      </header>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Your draft</CardTitle>
            <CardDescription>What you submitted.</CardDescription>
          </CardHeader>
          <CardBody>
            {doc.content_text ? (
              <pre className="whitespace-pre-wrap font-sans text-[15px] leading-relaxed text-ink">
                {doc.content_text}
              </pre>
            ) : (
              <p className="text-sm text-ink-subtle">
                Submitted as a file. Source preview unavailable.
              </p>
            )}
          </CardBody>
        </Card>

        <div className="space-y-4">
          {!fb ? (
            <Card>
              <CardBody className="py-10 text-center">
                <p className="font-display text-lg text-ink">
                  {doc.processing_status === "failed"
                    ? "Feedback generation failed."
                    : "Generating grounded feedback…"}
                </p>
                <p className="mt-2 text-sm text-ink-muted">
                  {doc.processing_status === "failed"
                    ? "Try re-running."
                    : "This usually takes 10-30 seconds."}
                </p>
              </CardBody>
            </Card>
          ) : (
            <FeedbackPartitions fb={fb} />
          )}
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ doc }: { doc: DocumentDetail }) {
  if (doc.processing_status === "completed") return <Badge tone="validated">Final</Badge>;
  if (doc.processing_status === "failed") return <Badge tone="danger">Failed — retry</Badge>;
  return <Badge tone="caution">Draft</Badge>;
}

function FeedbackPartitions({ fb }: { fb: DocumentFeedbackPartition }) {
  return (
    <>
      <Partition
        tone="validated"
        icon={<ShieldCheck className="size-4" strokeWidth={2} />}
        title="Validated facts"
        description="Verified scholarship rules."
      >
        {fb.validated_facts.length === 0 ? (
          <Empty>No validated facts cited.</Empty>
        ) : (
          <ul className="space-y-2">
            {fb.validated_facts.map((f, i) => (
              <li key={i} className="validated-stripe pl-3 text-sm">
                <span className="text-ink">{f.text}</span>
                {f.source_url ? (
                  <a
                    href={f.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-2 inline-flex items-center gap-0.5 text-xs text-ink-subtle hover:text-ink"
                  >
                    <ExternalLink className="size-3" strokeWidth={2} /> source
                  </a>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </Partition>

      <Partition
        tone="neutral"
        icon={<BookText className="size-4" strokeWidth={2} />}
        title="Retrieved writing guidance"
        description="From a vetted writing-guide library."
      >
        {fb.retrieved_writing_guidance.length === 0 ? (
          <Empty>No writing guidance retrieved.</Empty>
        ) : (
          <ul className="space-y-2">
            {fb.retrieved_writing_guidance.map((g, i) => (
              <li key={i} className="border-l border-[var(--color-border)] pl-3 text-sm">
                <span className="text-ink">{g.text}</span>
                {g.source ? <span className="ml-2 text-xs text-ink-subtle">— {g.source}</span> : null}
              </li>
            ))}
          </ul>
        )}
      </Partition>

      <Partition
        tone="generated"
        icon={<Sparkles className="size-4" strokeWidth={2} />}
        title="Generated guidance"
        description="AI-written suggestions. Not authoritative."
      >
        {fb.generated_guidance.length === 0 ? (
          <Empty>No generated suggestions.</Empty>
        ) : (
          <ul className="space-y-2">
            {fb.generated_guidance.map((g, i) => (
              <li key={i} className="generated-stripe pl-3 text-sm text-ink">
                {g.text}
              </li>
            ))}
          </ul>
        )}
      </Partition>

      <Partition
        tone="caution"
        icon={<AlertTriangle className="size-4" strokeWidth={2} />}
        title="Limitations"
        description="What this feedback does not cover."
      >
        {fb.limitations.length === 0 ? (
          <Empty>No limitations flagged.</Empty>
        ) : (
          <ul className="space-y-1 text-sm text-ink">
            {fb.limitations.map((l, i) => (
              <li key={i} className="caution-stripe pl-3">
                {l}
              </li>
            ))}
          </ul>
        )}
      </Partition>
    </>
  );
}

function Partition({
  tone,
  icon,
  title,
  description,
  children,
}: {
  tone: "validated" | "generated" | "caution" | "neutral";
  icon: React.ReactNode;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  const toneCls =
    tone === "validated"
      ? "validated-stripe"
      : tone === "generated"
        ? "generated-stripe"
        : tone === "caution"
          ? "caution-stripe"
          : "";
  return (
    <Card className={toneCls}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <span
            className={
              tone === "validated"
                ? "text-validated"
                : tone === "generated"
                  ? "text-generated"
                  : tone === "caution"
                    ? "text-caution"
                    : "text-ink-muted"
            }
          >
            {icon}
          </span>
          <CardTitle>{title}</CardTitle>
        </div>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardBody>{children}</CardBody>
    </Card>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-ink-subtle">{children}</p>;
}
