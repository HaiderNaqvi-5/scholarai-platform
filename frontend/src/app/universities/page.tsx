/**
 * /universities — public B2B institution-facing page (PRD §0.6).
 *
 * Trust boundary: no link from the student dashboard reaches here. The page
 * is a marketing surface and a mailto entry to partnerships@scholarai.pk.
 * The authenticated institution admin lives under `(partners)/`.
 */

import Link from "next/link";
import { ArrowRight, Building2, Layers3, Mail, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { partnershipsMailto, PARTNERSHIPS_EMAIL } from "@/lib/brand";

const PARTNERSHIPS_MAILTO = partnershipsMailto("Partnership Inquiry");

export default function UniversitiesPage() {
  return (
    <div className="min-h-screen bg-paper">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <Link href="/" className="font-display text-xl tracking-tight text-ink">
          AidwiseAI
        </Link>
        <nav className="flex items-center gap-2">
          <Button asChild variant="ghost" size="sm">
            <a href={PARTNERSHIPS_MAILTO}>
              <Mail className="size-4" aria-hidden /> Contact
            </a>
          </Button>
        </nav>
      </header>

      <section className="mx-auto max-w-5xl px-6 pb-16 pt-12 md:pt-24">
        <p className="font-mono text-xs uppercase tracking-[0.16em] text-ink-subtle">
          For universities, schools, and HEC partners
        </p>
        <h1 className="mt-3 max-w-3xl font-display text-[44px] font-semibold leading-[1.05] tracking-tight text-ink md:text-[60px]">
          Reach motivated Pakistani applicants.
          <span className="text-ink-muted"> With consent. With provenance.</span>
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-ink-muted">
          AidwiseAI runs a strict trust boundary: the matching algorithm has
          zero knowledge of partner agreements. We share student data only with
          explicit opt-in and a signed DPA — and only the snapshot taken at
          share time. No retro-leak. No silent re-share.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button asChild size="lg">
            <a href={PARTNERSHIPS_MAILTO}>
              Start a conversation <ArrowRight className="size-4" />
            </a>
          </Button>
          <Button asChild variant="secondary" size="lg">
            <Link href="/partners">Partner sign in</Link>
          </Button>
        </div>
      </section>

      <section className="border-t border-[var(--color-border)] bg-paper-warm/40">
        <div className="mx-auto grid max-w-6xl gap-4 px-6 py-16 md:grid-cols-3">
          <Pillar
            icon={<Building2 className="size-5" />}
            title="Foreign universities"
            body="Per-enrolled-student referral fees ($200–500). Pakistani students apply via AidwiseAI; you confirm enrolment; we invoice."
          />
          <Pillar
            icon={<Layers3 className="size-5" />}
            title="Pakistani schools / universities"
            body="Seat licence covering all your students. Bulk import, aggregate outcomes dashboard, co-branded career-centre portal."
          />
          <Pillar
            icon={<ShieldCheck className="size-5" />}
            title="Strict trust boundary"
            body="Student recommendations are physically isolated from B2B tables. PRD §0.6 — verified by CI AST guard."
          />
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 py-16">
        <h2 className="font-display text-3xl text-ink">How it works</h2>
        <ol className="mt-6 space-y-3 text-ink-muted">
          <li>
            <strong className="text-ink">1.</strong> Email partnerships and we
            send the DPA, data dictionary, and price grid for your use case.
          </li>
          <li>
            <strong className="text-ink">2.</strong> We co-sign the DPA and you
            get a partner account in <code>partners.scholarai.pk</code>.
          </li>
          <li>
            <strong className="text-ink">3.</strong> Students who opt in to B2B
            sharing become visible to your dashboard — only the fields they
            consented to, snapshotted at share time.
          </li>
          <li>
            <strong className="text-ink">4.</strong> Outcomes (offers,
            enrolments, referral fees) flow back into your admin view.
          </li>
        </ol>
      </section>

      <footer className="border-t border-[var(--color-border)]">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-8 text-sm text-ink-subtle md:flex-row md:items-center md:justify-between">
          <p>AidwiseAI · Institutional partnerships.</p>
          <p className="font-mono text-xs">
            <a href={PARTNERSHIPS_MAILTO} className="underline">
              {PARTNERSHIPS_EMAIL}
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}

function Pillar({
  icon,
  title,
  body,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
}) {
  return (
    <div className="rounded-[20px] border border-[var(--color-border)] bg-paper-white p-6">
      <span className="text-ink" aria-hidden>
        {icon}
      </span>
      <h3 className="mt-2 font-display text-lg text-ink">{title}</h3>
      <p className="mt-2 text-[15px] text-ink-muted">{body}</p>
    </div>
  );
}
