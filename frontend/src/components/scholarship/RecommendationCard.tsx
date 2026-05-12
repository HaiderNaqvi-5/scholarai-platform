"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Bookmark,
  BookmarkCheck,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Sparkles,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { EligibilityMatrix } from "./EligibilityMatrix";
import type { RecommendationItem, StudentProfile } from "@/lib/api";
import { formatAmount, formatDeadline } from "@/lib/utils";

const STAGE_LABELS: Record<string, string> = {
  scope: "Scope",
  eligibility: "Eligibility",
  retrieval: "Retrieval",
  rerank: "Rerank",
};

export function RecommendationCard({
  item,
  profile,
  saved,
  saving,
  onToggleSave,
}: {
  item: RecommendationItem;
  profile?: StudentProfile;
  saved?: boolean;
  saving?: boolean;
  onToggleSave?: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const s = item.scholarship;
  const dl = s.deadline ? formatDeadline(s.deadline) : null;
  const supporting = item.supporting_factors ?? [];
  const limiting = item.limiting_factors ?? [];

  return (
    <Card className="hover:border-ink-muted">
      <CardHeader className="flex-row items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 text-xs text-ink-subtle">
            <span className="font-mono">#{item.rank}</span>
            {s.published_at ? <span>· Published</span> : null}
          </div>
          <CardTitle className="mt-1 break-words">
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
        <div className="flex flex-wrap gap-1.5">
          {item.stages.map((stage) => (
            <Badge
              key={stage.name}
              tone={
                stage.status === "passed" || stage.status === "applied"
                  ? "validated"
                  : stage.status === "failed"
                    ? "danger"
                    : "neutral"
              }
              title={stage.detail}
            >
              {STAGE_LABELS[stage.name] ?? stage.name}
            </Badge>
          ))}
        </div>

        {supporting.length > 0 ? (
          <FactorList tone="validated" label="Supports" factors={supporting} />
        ) : null}
        {limiting.length > 0 ? (
          <FactorList tone="caution" label="Limits" factors={limiting} />
        ) : null}

        {expanded && profile ? (
          <div className="space-y-2">
            <p className="font-mono text-xs uppercase tracking-wider text-ink-subtle">
              Eligibility check
            </p>
            <EligibilityMatrix scholarship={s} profile={profile} />
          </div>
        ) : null}

        <div className="flex items-center justify-between gap-2 pt-1">
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="inline-flex items-center gap-1 text-xs text-ink-subtle hover:text-ink"
          >
            {expanded ? (
              <>
                <ChevronUp className="size-3.5" strokeWidth={2} /> Hide details
              </>
            ) : (
              <>
                <ChevronDown className="size-3.5" strokeWidth={2} /> Show eligibility check
              </>
            )}
          </button>
          <div className="flex items-center gap-2">
            {onToggleSave ? (
              <Button
                size="sm"
                variant={saved ? "validated" : "secondary"}
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
            ) : null}
            {s.source_url ? (
              <a
                href={s.source_url}
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Open source"
                className="inline-flex size-9 items-center justify-center rounded-[10px] text-ink-subtle hover:bg-paper-warm hover:text-ink"
              >
                <ExternalLink className="size-4" strokeWidth={2} />
              </a>
            ) : null}
          </div>
        </div>
        <p className="flex items-center gap-1.5 text-xs text-ink-subtle">
          <Sparkles className="size-3" strokeWidth={2} aria-hidden /> Ranked from your profile and
          published eligibility rules. Not an acceptance prediction.
        </p>
      </CardBody>
    </Card>
  );
}

function FactorList({
  tone,
  label,
  factors,
}: {
  tone: "validated" | "caution";
  label: string;
  factors: string[];
}) {
  return (
    <div className="text-sm">
      <p className="font-mono text-xs uppercase tracking-wider text-ink-subtle">{label}</p>
      <ul className="mt-1 space-y-1">
        {factors.map((f, i) => (
          <li
            key={i}
            className={`pl-3 ${tone === "validated" ? "validated-stripe" : "caution-stripe"}`}
          >
            {f}
          </li>
        ))}
      </ul>
    </div>
  );
}
