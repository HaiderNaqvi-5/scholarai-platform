"use client";

import Link from "next/link";
import { Bookmark, BookmarkCheck, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import type { Scholarship } from "@/lib/api";
import { formatAmount, formatDeadline } from "@/lib/utils";

export function ScholarshipCard({
  scholarship: s,
  saved,
  onToggleSave,
  saving,
}: {
  scholarship: Scholarship;
  saved?: boolean;
  onToggleSave?: () => void;
  saving?: boolean;
}) {
  const dl = s.deadline ? formatDeadline(s.deadline) : null;
  return (
    <Card className="hover:border-ink-muted">
      <CardHeader className="flex-row items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <CardTitle className="break-words">
            <Link
              href={`/scholarships/${s.id}`}
              className="hover:underline underline-offset-4"
            >
              {s.title}
            </Link>
          </CardTitle>
          <p className="mt-1 text-sm text-ink-muted">
            {s.provider} · {s.country_code} · {s.degree_level}
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
          <span className="font-mono text-sm text-ink">
            {formatAmount(s.amount_max ?? s.amount_min, s.currency || "CAD")}
          </span>
        </div>
      </CardHeader>
      <CardBody className="space-y-3">
        {s.field_tags.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {s.field_tags.slice(0, 4).map((t) => (
              <Badge key={t} tone="neutral">
                {t}
              </Badge>
            ))}
            {s.field_tags.length > 4 ? (
              <Badge tone="neutral">+{s.field_tags.length - 4}</Badge>
            ) : null}
          </div>
        ) : null}
        {s.description ? (
          <p className="line-clamp-2 text-sm text-ink-muted">{s.description}</p>
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
          {s.source_url ? (
            <a
              href={s.source_url}
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
