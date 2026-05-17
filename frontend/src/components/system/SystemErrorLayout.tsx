import type { ReactNode } from "react";
import Link from "next/link";

interface SystemErrorLayoutProps {
  title: string;
  description: string;
  primary?: { href: string; label: string };
  secondary?: { href?: string; label: string; mailto?: string };
  meta?: ReactNode;
}

/**
 * Shared centered layout for /404 /500 /denied /offline /maintenance
 * (Front-upgrade §6.32-36).
 *
 * Ivory background, Fraunces italic title at 32, ink-muted description,
 * one primary + one secondary CTA. No illustration, no emoji.
 */
export function SystemErrorLayout({
  title,
  description,
  primary,
  secondary,
  meta,
}: SystemErrorLayoutProps) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--color-ivory)] px-6">
      <div className="max-w-[520px] text-center">
        <h1 className="font-display text-[32px] italic leading-[1.1] tracking-[-0.02em] text-ink-deep">
          {title}
        </h1>
        <p className="mt-4 text-[15px] leading-[1.6] text-ink-muted">{description}</p>
        {meta ? <div className="mt-4 text-[13px] font-mono text-ink-subtle">{meta}</div> : null}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          {primary ? (
            <Link
              href={primary.href}
              className="inline-flex h-11 items-center justify-center rounded-[12px] bg-ink-deep px-5 text-[14px] font-medium text-paper-white hover:bg-ink"
            >
              {primary.label}
            </Link>
          ) : null}
          {secondary ? (
            secondary.mailto ? (
              <a
                href={`mailto:${secondary.mailto}`}
                className="inline-flex h-11 items-center justify-center rounded-[12px] border border-[var(--color-border)] bg-paper-white px-5 text-[14px] font-medium text-ink-deep hover:bg-paper-warm"
              >
                {secondary.label}
              </a>
            ) : secondary.href ? (
              <Link
                href={secondary.href}
                className="inline-flex h-11 items-center justify-center rounded-[12px] border border-[var(--color-border)] bg-paper-white px-5 text-[14px] font-medium text-ink-deep hover:bg-paper-warm"
              >
                {secondary.label}
              </Link>
            ) : null
          ) : null}
        </div>
      </div>
    </main>
  );
}
