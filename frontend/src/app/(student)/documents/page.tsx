"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { FileText, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { endpoints } from "@/lib/api";
import type { DocumentStatus } from "@/lib/api";

const STATUS_TONE: Record<DocumentStatus, "neutral" | "validated" | "caution" | "danger"> = {
  pending: "neutral",
  processing: "caution",
  completed: "validated",
  failed: "danger",
};

const STATUS_LABEL: Record<DocumentStatus, string> = {
  pending: "Pending",
  processing: "Generating feedback…",
  completed: "Feedback ready",
  failed: "Failed",
};

export default function DocumentsPage() {
  const docsQ = useQuery({
    queryKey: ["documents"],
    queryFn: endpoints.documents.list,
  });

  return (
    <div className="mx-auto max-w-4xl">
      <header className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-ink">Documents</h1>
          <p className="mt-1 text-ink-muted">
            Drafts and statements you&apos;ve submitted for grounded feedback.
          </p>
        </div>
        <Button asChild>
          <Link href="/documents/new">
            <Plus className="size-4" strokeWidth={2} /> New
          </Link>
        </Button>
      </header>

      {docsQ.isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      ) : docsQ.isError ? (
        <Empty
          title="Couldn't load documents."
          body="Try again."
          cta={{ label: "Retry", onClick: () => docsQ.refetch() }}
        />
      ) : !docsQ.data || docsQ.data.items.length === 0 ? (
        <Empty
          title="No documents yet"
          body="Paste your statement of purpose or upload a .pdf/.docx to get grounded feedback against a target scholarship."
          cta={{ label: "Start one", href: "/documents/new" }}
        />
      ) : (
        <ul className="space-y-3">
          {docsQ.data.items.map((d) => (
            <li key={d.id}>
              <Link href={`/documents/${d.id}`} className="block">
                <Card className="hover:border-ink-muted">
                  <CardHeader className="flex-row items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <FileText className="mt-1 size-5 text-ink-muted" strokeWidth={2} />
                      <div>
                        <CardTitle>{d.title}</CardTitle>
                        <p className="mt-1 text-sm text-ink-muted">
                          {d.document_type} · Updated{" "}
                          {new Date(d.updated_at ?? d.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <Badge tone={STATUS_TONE[d.processing_status]}>
                      {STATUS_LABEL[d.processing_status]}
                    </Badge>
                  </CardHeader>
                  {d.scholarship_ids && d.scholarship_ids.length > 0 ? (
                    <CardBody>
                      <p className="text-xs text-ink-subtle">
                        Grounded against {d.scholarship_ids.length} scholarship
                        {d.scholarship_ids.length === 1 ? "" : "s"}
                      </p>
                    </CardBody>
                  ) : null}
                </Card>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Empty({
  title,
  body,
  cta,
}: {
  title: string;
  body: string;
  cta?: { label: string; href?: string; onClick?: () => void };
}) {
  return (
    <div className="rounded-[20px] border border-[var(--color-border)] bg-paper-white p-10 text-center">
      <h2 className="font-display text-xl text-ink">{title}</h2>
      <p className="mt-2 text-ink-muted">{body}</p>
      {cta ? (
        <div className="mt-5">
          {cta.href ? (
            <Button asChild>
              <Link href={cta.href}>{cta.label}</Link>
            </Button>
          ) : (
            <Button onClick={cta.onClick}>{cta.label}</Button>
          )}
        </div>
      ) : null}
    </div>
  );
}
