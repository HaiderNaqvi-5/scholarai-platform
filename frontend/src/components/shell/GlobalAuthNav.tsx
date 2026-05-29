"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { SignedIn, SignedOut, UserButton } from "@clerk/nextjs";

/**
 * Top-right auth control for bare public routes (legal, upgrade, system
 * pages) that have no chrome of their own. Suppressed on routes that
 * already render a dedicated header — landing, the auth flow, and any
 * route under the app shell — to avoid a duplicate nav cluster.
 */
const SUPPRESS_PREFIXES = ["/login", "/signup", "/onboarding", "/sso-callback"];

export function GlobalAuthNav() {
  const pathname = usePathname();
  const suppressed =
    pathname === "/" || SUPPRESS_PREFIXES.some((p) => pathname.startsWith(p));
  if (suppressed) return null;

  return (
    <header className="flex items-center justify-end gap-3 px-6 py-3 md:px-12">
      <SignedOut>
        <Link
          href="/login"
          className="inline-flex min-h-[44px] items-center text-[13px] text-ink-muted hover:text-ink-deep"
        >
          Sign in
        </Link>
        <Link
          href="/signup"
          className="inline-flex min-h-[44px] items-center rounded-[10px] bg-lapis px-4 text-[13px] font-medium text-paper-white hover:bg-ink-deep"
        >
          Create account
        </Link>
      </SignedOut>
      <SignedIn>
        <UserButton />
      </SignedIn>
    </header>
  );
}
