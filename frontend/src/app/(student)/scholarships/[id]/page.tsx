"use client";

import { use } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Bookmark, BookmarkCheck, ExternalLink, FileText, MessageSquare } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { AsideAtAGlance } from "@/components/scholarship/AsideAtAGlance";
import { endpoints } from "@/lib/api";
import { formatAmount, formatDeadline } from "@/lib/utils";

export default function ScholarshipDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const qc = useQueryClient();

  const detailQ = useQuery({
    queryKey: ["scholarship", id],
    queryFn: () => endpoints.scholarships.detail(id),
  });

  const savedQ = useQuery({
    queryKey: ["saved"],
    queryFn: endpoints.saved.list,
  });
  const isSaved = savedQ.data?.items.some((s) => s.scholarship_id === id) ?? false;

  const toggleSave = useMutation({
    mutationFn: async () => {
      if (isSaved) await endpoints.saved.remove(id);
      else await endpoints.saved.add(id);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["saved"] });
      toast.success(isSaved ? "Removed from saved." : "Saved.");
    },
    onError: () => toast.error("Couldn't update saved list."),
  });

  if (detailQ.isLoading) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (detailQ.isError || !detailQ.data) {
    return (
      <div className="mx-auto max-w-3xl rounded-[20px] border border-[var(--color-border)] bg-paper-white p-10 text-center">
        <h2 className="font-display text-xl text-ink">Scholarship not found.</h2>
        <p className="mt-2 text-ink-muted">It may have been unpublished or removed.</p>
        <div className="mt-5">
          <Button asChild>
            <Link href="/discover">
              <ArrowLeft className="size-4" strokeWidth={2} /> Back to discover
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  const s = detailQ.data;
  const dl = s.deadline ? formatDeadline(s.deadline) : null;

  return (
    <div className="mx-auto max-w-[1200px]">
      <Link
        href="/discover"
        className="inline-flex items-center gap-1 text-[13px] text-ink-muted hover:text-ink-deep"
      >
        <ArrowLeft className="size-4" strokeWidth={1.5} /> Discover
      </Link>

      <div className="mt-4 grid gap-8 lg:grid-cols-[1fr_320px]">
        <div className="min-w-0">
          <header className="validated-stripe space-y-3 pl-5">
            <h1 className="font-display text-[32px] italic font-[450] leading-[1.1] tracking-[-0.02em] text-ink-deep">
              {s.title}
            </h1>
            <p className="text-[14px] text-ink-muted">
              {s.provider} · {s.country_code} · {s.degree_level}
            </p>
            <div className="flex flex-wrap items-center gap-2">
              {dl ? (
                <Badge
                  tone={
                    dl.tone === "urgent"
                      ? "caution"
                      : dl.tone === "passed"
                        ? "sindoor"
                        : "validated"
                  }
                >
                  {dl.label}
                </Badge>
              ) : null}
              <Badge tone="neutral">{s.funding_type}</Badge>
              <span className="font-mono text-[13px] tabular-nums text-ink-deep">
                {formatAmount(s.amount_max ?? s.amount_min, s.currency || "GBP")}
              </span>
            </div>
            <div className="flex flex-wrap gap-2 pt-2">
              <Button
                variant={isSaved ? "validated" : "primary"}
                onClick={() => toggleSave.mutate()}
                loading={toggleSave.isPending}
              >
                {isSaved ? (
                  <>
                    <BookmarkCheck className="size-4" strokeWidth={1.5} /> Saved
                  </>
                ) : (
                  <>
                    <Bookmark className="size-4" strokeWidth={1.5} /> Save
                  </>
                )}
              </Button>
              <Button asChild variant="secondary">
                <Link href={`/documents/sop?scholarship=${s.id}`}>
                  <FileText className="size-4" strokeWidth={1.5} /> Draft SOP
                </Link>
              </Button>
              <Button asChild variant="secondary">
                <Link href={`/interviews/visa?scholarship=${s.id}`}>
                  <MessageSquare className="size-4" strokeWidth={1.5} /> Practice interview
                </Link>
              </Button>
              {s.source_url ? (
                <Button asChild variant="ghost">
                  <a href={s.source_url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="size-4" strokeWidth={1.5} /> Source
                  </a>
                </Button>
              ) : null}
            </div>
          </header>

          <div className="mt-8 space-y-5">
            {s.description ? (
              <Card>
                <CardHeader>
                  <CardTitle>About</CardTitle>
                </CardHeader>
                <CardBody className="space-y-3 whitespace-pre-line text-ink">
                  {s.description}
                </CardBody>
              </Card>
            ) : null}

            <Card>
              <CardHeader>
                <CardTitle>Eligibility</CardTitle>
              </CardHeader>
              <CardBody>
                <table className="w-full text-left text-[14px]">
                  <caption className="sr-only">Eligibility requirements</caption>
                  <tbody>
                    <FactRow
                      label="Citizenship"
                      value={
                        s.citizenship_rules && s.citizenship_rules.length > 0
                          ? s.citizenship_rules.join(", ")
                          : "Not specified"
                      }
                    />
                    <FactRow
                      label="Min GPA"
                      value={s.min_gpa != null ? String(s.min_gpa) : "Not specified"}
                    />
                    <FactRow
                      label="Field tags"
                      value={s.field_tags.length > 0 ? s.field_tags.join(", ") : "Any field"}
                    />
                    {s.language_requirements && s.language_requirements.length > 0 ? (
                      <FactRow
                        label="Language"
                        value={s.language_requirements
                          .map((l) => `${l.test} ${l.min_score}+`)
                          .join(", ")}
                      />
                    ) : null}
                  </tbody>
                </table>
              </CardBody>
            </Card>

            {s.requirements && s.requirements.length > 0 ? (
              <Card>
                <CardHeader>
                  <CardTitle>Requirements</CardTitle>
                </CardHeader>
                <CardBody>
                  <ul className="space-y-1 text-ink">
                    {s.requirements.map((r, i) => (
                      <li key={i} className="validated-stripe pl-3">
                        {r}
                      </li>
                    ))}
                  </ul>
                </CardBody>
              </Card>
            ) : null}
          </div>
        </div>

        <AsideAtAGlance scholarship={s} />
      </div>
    </div>
  );
}

function FactRow({ label, value }: { label: string; value: string }) {
  return (
    <tr className="border-b border-[var(--color-border-quiet)] last:border-b-0">
      <th
        scope="row"
        className="py-2 pr-4 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle"
      >
        {label}
      </th>
      <td className="py-2 text-right text-[14px] text-ink">{value}</td>
    </tr>
  );
}
