/**
 * `(partners)` route group — institution admin surface (PRD §0.6).
 *
 * Trust boundary:
 * - PARTNER_ROLES excludes every student role (see RoleGuard).
 * - No student layout / sidebar / nav reaches here.
 * - Route URLs are not linked from any student-side surface; the only entry
 *   point is /universities → "Partner sign in".
 */

import Link from "next/link";
import { RoleGuard } from "@/lib/auth/RoleGuard";

export default function PartnersLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleGuard group="partner">
      <div className="min-h-screen bg-paper">
        <header className="border-b border-[var(--color-border)] bg-paper-white">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
            <Link href="/partners" className="font-display text-lg text-ink">
              AidwiseAI · Partners
            </Link>
            <nav className="flex items-center gap-4 text-sm">
              <Link href="/partners" className="text-ink-muted hover:text-ink">
                Overview
              </Link>
              <Link
                href="/partners/universities"
                className="text-ink-muted hover:text-ink"
              >
                Universities
              </Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-10">{children}</main>
      </div>
    </RoleGuard>
  );
}
