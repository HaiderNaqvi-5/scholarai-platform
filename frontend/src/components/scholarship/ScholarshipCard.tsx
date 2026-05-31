"use client";

import Link from "next/link";
import { Bookmark, BookmarkCheck, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import type { ScholarshipListItem } from "@/lib/api";
import { formatAmount, formatDeadline, safeHttpUrl } from "@/lib/utils";

export function ScholarshipCard({
  scholarship: s,
  saved,
  onToggleSave,
  saving,
}: {
  scholarship: ScholarshipListItem;
  saved?: boolean;
  onToggleSave?: () => void;
  saving?: boolean;
}) {
  const dl = s.deadline_at ? formatDeadline(s.deadline_at) : null;
  const degree = s.degree_levels?.[0];
  const tags = s.field_tags ?? [];
  const funding = s.funding_summary ?? formatAmount(s.funding_amount_max ?? s.funding_amount_min);
  return (
    <Card className="hover:border-ink-muted">
      <CardHeader className="flex-row items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <CardTitle className="break-words">
            <Link
              href={`/scholarships/${s.scholarship_id}`}
              className="hover:underline underline-offset-4"
            >
              {s.title}
            </Link>
          </CardTitle>
          <p className="mt-1 text-sm text-ink-muted">
            {[s.provider_name, s.country_code, degree].filter(Boolean).join(" · ")}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1.5">
          {dl ? (
            <Badge
              tone={
                dl.tone === "urgent"
                  ? "caution"
                  : dl.tone === "passed"
                    ? "danger"
                    : "neutral"
              }
            >
              {dl.label}
            </Badge>
          ) : null}
          <span className="font-mono text-sm text-ink">{funding}</span>
        </div>
      </CardHeader>
      <CardBody className="space-y-3">
        {tags.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {tags.slice(0, 4).map((t) => (
              <Badge key={t} tone="neutral">
                {t}
              </Badge>
            ))}
            {tags.length > 4 ? (
              <Badge tone="neutral">+{tags.length - 4}</Badge>
            ) : null}
          </div>
        ) : null}
        {s.summary ? (
          <p className="line-clamp-2 text-sm text-ink-muted">{s.summary}</p>
        ) : null}
        <div className="flex items-center justify-between gap-2">
          {onToggleSave ? (
            <Button
              variant={saved ? "validated" : "secondary"}
              size="sm"
              onClick={onToggleSave}
              loading={saving}
            >
              {saved ? (
                <>
                  <BookmarkCheck className="size-4" strokeWidth={2} /> Saved
                </>
              ) : (
                <>
                  <Bookmark className="size-4" strokeWidth={2} /> Save
                </>
              )}
            </Button>
          ) : (
            <span />
          )}
          {safeHttpUrl(s.source_url) ? (
            <a
              href={safeHttpUrl(s.source_url)!}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-ink-subtle hover:text-ink"
            >
              <ExternalLink className="size-3" strokeWidth={2} />
              Source
            </a>
          ) : null}
        </div>
      </CardBody>
    </Card>
  );
}
