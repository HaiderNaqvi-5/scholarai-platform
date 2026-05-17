"use client";

import type { Scholarship } from "@/lib/api/types";
import { formatAmount, formatDeadline } from "@/lib/utils";

interface AsideAtAGlanceProps {
  scholarship: Scholarship;
  /** Optional 0..1 compatibility from POST /scholarships/match */
  compatibility?: number | null;
}

/**
 * "At a glance" right-hand aside (Front-upgrade §6.10). Sticky on lg+.
 * Composes: deadline countdown / funding summary / compatibility / source link.
 *
 * Anti-slop: never label compatibility as "acceptance prediction" — the
 * exact verbatim string is "Estimated Scholarship Fit Score" per §6.10.
 */
export function AsideAtAGlance({ scholarship, compatibility }: AsideAtAGlanceProps) {
  const dl = scholarship.deadline ? formatDeadline(scholarship.deadline) : null;
  const fundLabel = scholarship.amount_max ?? scholarship.amount_min;
  return (
    <aside
      aria-label="Scholarship summary"
      className="rounded-[18px] border border-[var(--color-border)] bg-paper-white p-5 lg:sticky lg:top-24"
    >
      <p className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
        At a glance
      </p>

      <dl className="mt-4 space-y-4 text-[13px]">
        <div>
          <dt className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
            Deadline
          </dt>
          <dd className="mt-1 font-mono text-[14px] tabular-nums text-ink-deep">
            {dl ? dl.label : "Rolling"}
          </dd>
        </div>

        <div>
          <dt className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
            Funding
          </dt>
          <dd className="mt-1 font-mono text-[14px] tabular-nums text-ink-deep">
            {fundLabel != null
              ? formatAmount(fundLabel, scholarship.currency || "GBP")
              : "Disclosed at offer"}
          </dd>
          <dd className="mt-0.5 text-[12px] text-ink-muted">{scholarship.funding_type}</dd>
        </div>

        {compatibility != null ? (
          <div>
            <dt className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
              Estimated Scholarship Fit Score
            </dt>
            <dd className="mt-1 font-mono text-[14px] tabular-nums text-ink-deep">
              {Math.round(Math.max(0, Math.min(1, compatibility)) * 100)}%
            </dd>
            <dd className="mt-0.5 text-[12px] text-ink-muted">
              Estimated fit. Never an acceptance prediction.
            </dd>
          </div>
        ) : null}

        {scholarship.source_url ? (
          <div>
            <dt className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
              Source
            </dt>
            <dd className="mt-1">
              <a
                href={scholarship.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="break-all text-[12px] text-lapis underline underline-offset-2 hover:decoration-2"
              >
                {scholarship.source_url.replace(/^https?:\/\//, "")}
              </a>
            </dd>
            {scholarship.published_at ? (
              <dd className="mt-1 font-mono text-[11px] text-ink-subtle">
                Last verified{" "}
                {new Date(scholarship.published_at).toLocaleDateString("en-GB", {
                  year: "numeric",
                  month: "short",
                  day: "numeric",
                })}
              </dd>
            ) : null}
          </div>
        ) : null}
      </dl>
    </aside>
  );
}
