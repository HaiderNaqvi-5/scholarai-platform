"use client";

import Link from "next/link";

type SubNavLink = { href: string; label: string; emphasis?: boolean };

const LINKS: SubNavLink[] = [
  { href: "#how", label: "How it works" },
  { href: "#scholarships", label: "Scholarships" },
  { href: "/upgrade", label: "Pricing" },
  { href: "/login", label: "Sign in" },
  { href: "/signup", label: "Get started", emphasis: true },
];

/**
 * Mobile-only secondary nav. The landing header drops the two anchor links
 * (#how, #scholarships) at <md to keep the brand row clean; this bar
 * surfaces them in a horizontal scroll-snap row directly under the header.
 *
 * Hidden on md+ where the header carries all 5 links.
 *
 * Motion: none — frequent visibility (every mobile visitor on /) means
 * animation would feel sluggish (per emil-design-eng "Should this animate
 * at all?"). Only colour transition on hover.
 */
export function StickySubNav() {
  return (
    <nav
      aria-label="Section shortcuts"
      className="sticky top-[57px] z-20 -mt-px border-b border-[var(--color-border-quiet)] bg-ivory md:hidden"
    >
      <ul className="mx-auto flex max-w-[1200px] snap-x snap-mandatory items-center gap-1 overflow-x-auto px-4 py-2.5">
        {LINKS.map((l) => (
          <li key={l.href} className="snap-start shrink-0">
            <Link
              href={l.href}
              className={
                l.emphasis
                  ? "inline-flex h-9 items-center rounded-full bg-ink-deep px-3.5 font-mono text-[11px] font-medium uppercase tracking-[0.06em] text-paper-white"
                  : "inline-flex h-9 items-center rounded-full px-3 font-mono text-[11px] font-medium uppercase tracking-[0.06em] text-ink-muted transition-colors duration-150 hover:text-lapis"
              }
            >
              {l.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
