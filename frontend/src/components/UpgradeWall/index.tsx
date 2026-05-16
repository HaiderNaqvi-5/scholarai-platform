"use client";

/**
 * UpgradeWall — the single surface for HTTP 402 plan gates (PRD §0.5).
 *
 * Never hides a feature. When `children` are supplied they render dimmed and
 * blurred behind the wall so the user sees exactly what they are missing.
 * Consumes the `PlanRequiredDetail` from `core/plan_guard.py` verbatim:
 * `message` and `price` are already currency-correct from the backend.
 */

import Link from "next/link";
import { Lock, Sparkles } from "lucide-react";
import type { PlanRequiredDetail, PlanRequiredPartialSummary } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type UpgradeWallProps = {
  detail: PlanRequiredDetail;
  /** Feature name for the eyebrow label, e.g. "Application tracker". */
  featureName?: string;
  /** Show the secondary "Or get Elite" CTA (SOP + visa interview only). */
  showElite?: boolean;
  /** The locked feature — rendered blurred behind the wall when provided. */
  children?: React.ReactNode;
  /**
   * When false, render a static placeholder behind the wall instead of
   * mounting the children tree. Pages whose locked feature kicks off queries
   * / mutations on mount should pass `false` to avoid wasted work behind a
   * gate the user can't cross.
   */
  mountChildren?: boolean;
  className?: string;
};

function PartialSummary({ summary }: { summary: PlanRequiredPartialSummary }) {
  // The visa-interview Q3 cut-off attaches a partial_summary. Render the few
  // fields we know are safe; ignore anything else the backend may add.
  const { red_flag_count: redFlags, answered, average_score: avg } = summary;
  if (redFlags == null && answered == null && avg == null) return null;
  return (
    <dl className="mt-4 grid grid-cols-3 gap-3 text-center">
      {answered != null && (
        <div className="rounded-[12px] bg-paper-warm p-3">
          <dt className="font-mono text-xs uppercase text-ink-muted">Answered</dt>
          <dd className="font-display text-xl text-ink">{answered}</dd>
        </div>
      )}
      {avg != null && (
        <div className="rounded-[12px] bg-paper-warm p-3">
          <dt className="font-mono text-xs uppercase text-ink-muted">Avg score</dt>
          <dd className="font-display text-xl text-ink">{avg.toFixed(1)}</dd>
        </div>
      )}
      {redFlags != null && (
        <div className="rounded-[12px] bg-paper-warm p-3">
          <dt className="font-mono text-xs uppercase text-ink-muted">Red flags</dt>
          <dd className="font-display text-xl text-danger">{redFlags}</dd>
        </div>
      )}
    </dl>
  );
}

function WallCard({
  detail,
  featureName,
  showElite,
}: Pick<UpgradeWallProps, "detail" | "featureName" | "showElite">) {
  const partial = detail.partial_summary ?? null;
  return (
    <div className="w-full max-w-md rounded-[20px] border border-[var(--color-border)] bg-paper-white p-6 shadow-[0_8px_30px_rgba(12,17,23,0.07)]">
      <div className="flex size-10 items-center justify-center rounded-full bg-paper-warm">
        <Lock className="size-5 text-ink" aria-hidden />
      </div>
      {featureName && (
        <p className="mt-3 font-mono text-xs uppercase tracking-wide text-ink-muted">
          {featureName}
        </p>
      )}
      <h3 className="mt-1 font-display text-xl leading-snug text-ink">
        {detail.message}
      </h3>
      {partial && <PartialSummary summary={partial} />}
      <div className="mt-5 flex flex-col gap-2">
        <Button asChild>
          <Link href={`/upgrade?plan=pro`}>Upgrade to Pro — {detail.price} →</Link>
        </Button>
        {showElite && (
          <Button asChild variant="secondary">
            <Link href={`/upgrade?plan=elite`}>
              <Sparkles className="size-4" aria-hidden />
              Or get Elite for full AI feedback
            </Link>
          </Button>
        )}
      </div>
      <p className="mt-3 text-center text-xs text-ink-muted">
        No consultant. No hidden fees. Cancel anytime.
      </p>
    </div>
  );
}

export function UpgradeWall({
  detail,
  featureName,
  showElite = false,
  children,
  mountChildren = false,
  className,
}: UpgradeWallProps) {
  const card = (
    <WallCard detail={detail} featureName={featureName} showElite={showElite} />
  );

  // Standalone — no feature behind it (e.g. a whole gated page).
  if (!children) {
    return <div className={cn("flex justify-center py-10", className)}>{card}</div>;
  }

  // Overlay — feature renders blurred behind the wall. Mount the children tree
  // only if explicitly requested; otherwise show a static placeholder block so
  // children's effects/queries don't fire behind a wall the user can't cross.
  return (
    <div className={cn("relative", className)}>
      <div aria-hidden className="pointer-events-none select-none blur-sm opacity-50">
        {mountChildren ? children : <div className="h-64 w-full rounded-[16px] bg-paper-warm/60" />}
      </div>
      <div className="absolute inset-0 flex items-center justify-center p-4">
        {card}
      </div>
    </div>
  );
}
