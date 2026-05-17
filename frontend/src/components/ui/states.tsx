import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * Empty / Error / Locked state primitives (Front-upgrade §4.2).
 *
 * Each is a vertical layout with an optional Lucide icon (32px), a
 * 17/600 title, a 14/400 ink-muted description, and an optional CTA
 * cluster. Renders inline within a Card or full-screen.
 *
 * Per the anti-slop charter: NEVER use illustration in empty states.
 * Never write "No data." — name what's missing.
 */

interface StateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  /** Full-screen rendering (page-level) instead of inline-within-card. */
  full?: boolean;
  className?: string;
}

export function EmptyState({ icon, title, description, action, full, className }: StateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center",
        full ? "min-h-[400px] py-16" : "py-10",
        className,
      )}
      role="status"
    >
      {icon ? (
        <span className="mb-4 text-ink-subtle" aria-hidden>
          {icon}
        </span>
      ) : null}
      <p className="text-[17px] font-semibold leading-tight text-ink-deep">{title}</p>
      {description ? (
        <p className="mt-2 max-w-md text-[14px] leading-[1.55] text-ink-muted">
          {description}
        </p>
      ) : null}
      {action ? <div className="mt-5 flex flex-wrap items-center justify-center gap-2">{action}</div> : null}
    </div>
  );
}

/**
 * ErrorState — sindoor icon, ink-deep title, retry CTA. Use after a network
 * failure. Inline within the failing card; full-page only when the whole
 * route can't render.
 */
export function ErrorState({ icon, title, description, action, full, className }: StateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center",
        full ? "min-h-[400px] py-16" : "py-10",
        className,
      )}
      role="alert"
    >
      {icon ? (
        <span className="mb-4 text-sindoor" aria-hidden>
          {icon}
        </span>
      ) : null}
      <p className="text-[17px] font-semibold leading-tight text-ink-deep">{title}</p>
      {description ? (
        <p className="mt-2 max-w-md text-[14px] leading-[1.55] text-ink-muted">
          {description}
        </p>
      ) : null}
      {action ? <div className="mt-5 flex flex-wrap items-center justify-center gap-2">{action}</div> : null}
    </div>
  );
}
