import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * SectionHeader — used inside interior pages above a card grid or list.
 * Eyebrow + h2 + optional description + optional right-aligned actions.
 * The eyebrow uses uppercase mono microlabel per Front-upgrade §2.2.
 */
interface SectionHeaderProps {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
  /** When true, use Fraunces italic on the h2 (editorial pages). */
  italic?: boolean;
  className?: string;
}

export function SectionHeader({
  eyebrow,
  title,
  description,
  actions,
  italic,
  className,
}: SectionHeaderProps) {
  return (
    <div
      className={cn(
        "mb-6 flex flex-col gap-2 md:mb-8 md:flex-row md:items-end md:justify-between",
        className,
      )}
    >
      <div>
        {eyebrow ? (
          <p className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
            {eyebrow}
          </p>
        ) : null}
        <h2
          className={cn(
            "mt-1 text-[24px] leading-[1.2] tracking-[-0.02em] text-ink-deep",
            italic && "italic font-[450]",
          )}
        >
          {title}
        </h2>
        {description ? (
          <p className="mt-2 max-w-prose text-[15px] text-ink-muted">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </div>
  );
}

/**
 * PageHeader — the H1 at the top of interior routes (`/feed`, `/tracker`,
 * `/upgrade`). Tighter scale than the marketing hero. Sentence case.
 */
export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  italic,
  className,
}: SectionHeaderProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-3 border-b border-[var(--color-border-quiet)] pb-6 md:flex-row md:items-end md:justify-between",
        className,
      )}
    >
      <div>
        {eyebrow ? (
          <p className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
            {eyebrow}
          </p>
        ) : null}
        <h1
          className={cn(
            "mt-1 text-[32px] leading-[1.15] tracking-[-0.02em] text-ink-deep",
            italic && "italic font-[450]",
          )}
        >
          {title}
        </h1>
        {description ? (
          <p className="mt-2 max-w-prose text-[15px] text-ink-muted">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </div>
  );
}
