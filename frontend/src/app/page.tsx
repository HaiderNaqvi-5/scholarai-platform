import Link from "next/link";
import {
  ArrowRight,
  Coins,
  FileSignature,
  Plane,
  CheckCircle2,
  Building2,
  CalendarRange,
  Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardEyebrow } from "@/components/ui/card";
import { StatChip } from "@/components/ui/stat-chip";
import { BRAND_DISPLAY_NAME } from "@/lib/brand";
import { RotatingDegree } from "@/components/marketing/RotatingDegree";

/**
 * Marketing landing (Front-upgrade §6.1).
 *
 * Goal: convert a Pakistani student visiting AidwiseAI for the first
 * time into a signup within 90 seconds. Editorial Premium Cultural
 * surface — Fraunces 56 italic h1, ivory page, lapis accents, named
 * providers (Chevening / Fulbright / DAAD / HEC).
 *
 * Per-screen anti-slop bans: hero gradient blob, "Revolutionary",
 * sparkle near "AI-powered", auto-scroll testimonial carousel. Per
 * §2.4 motion: hero fade-only on load (no slide), featured cards
 * stagger 60ms on viewport intersection — that stagger lives in the
 * CSS `fade-up` utility via `animation-delay` style.
 */

const PROVIDERS = [
  { name: "Chevening", country: "United Kingdom", funding: "Full tuition + £18,000/yr + travel" },
  { name: "Fulbright", country: "United States", funding: "Full tuition + $35,000/yr + health" },
  { name: "DAAD", country: "Germany", funding: "€934/mo + travel + insurance" },
  { name: "Commonwealth", country: "United Kingdom", funding: "Full tuition + monthly stipend" },
  { name: "HEC Overseas", country: "Pakistan → multi", funding: "Full PhD funding for 4 years" },
  { name: "Erasmus Mundus", country: "EU consortium", funding: "Full tuition + €1,400/mo" },
];

const STEPS = [
  {
    n: "01",
    title: "Set up your profile.",
    body: "Citizenship, CGPA on its native scale, target degree, target country. About four minutes.",
  },
  {
    n: "02",
    title: "Get your matches.",
    body: "We score every live scholarship against your profile. Eligible, partial, stretch. No filler.",
  },
  {
    n: "03",
    title: "Draft a Pakistan-context SOP.",
    body: "Paragraph by paragraph, with named providers and return-intent framing. You stay the author.",
  },
  {
    n: "04",
    title: "Practise the visa interview.",
    body: "Seventy questions across UK, US, Canada, Germany. With a rubric, not a thumbs-up.",
  },
];

const FAQS = [
  {
    q: "Is AidwiseAI really free?",
    a: "Yes. The Explorer tier stays free forever: 3 matches, 1 lifetime SOP, and 3 UK visa questions. Pro (PKR 2,999/mo) and Elite (PKR 6,000/mo) unlock the full match list, monthly SOPs, and all four country banks. No card needed to sign up.",
  },
  {
    q: "How is this different from a consultant?",
    a: "Consultants in Karachi or Lahore charge PKR 40,000–150,000 for a templated SOP and the same six universities they recommend to every client. We score every live scholarship against your real CGPA, target field, and household budget. You stay the author of every word. The recommendations show their working.",
  },
  {
    q: "Which scholarships and countries do you cover?",
    a: "20 active fully-funded scholarships and 47 universities across the UK, US, Canada, Germany, and Australia. Named providers include Chevening, Fulbright, DAAD, Commonwealth, HEC Overseas, and Erasmus Mundus. Listings are validated weekly and any change in deadline or funding gets re-verified.",
  },
  {
    q: "How accurate is the match score?",
    a: "The score is an Estimated Scholarship Fit Score — a structured comparison of your profile against the published eligibility rules, weighted by CGPA, target country, field, and language test. It is never an acceptance prediction. Every match shows the rule it matched, so you can audit the score yourself.",
  },
  {
    q: "What happens to my data?",
    a: "We follow Pakistan's PDPB. We never collect religion, politics, or biometric categories. Profile snapshots are only shared with universities you explicitly opt into on a per-share basis, and never until the institution has signed a DPA. You can export or delete your account from Settings → Danger zone (30-day cancellable window).",
  },
  {
    q: "When do I have to pay?",
    a: "Never if you stay on Explorer. Pro and Elite are currently on a waitlist — we open seats in cohorts and email you when one is yours. When billing opens we accept JazzCash, Easypaisa, and IBAN bank transfer in PKR; cards in GBP, EUR, AED, and USD.",
  },
];

const PROBLEMS = [
  {
    icon: <Plane className="size-6" strokeWidth={1.5} />,
    title: "Visa rejection is the silent tax.",
    body: "Pakistan sits among the lowest UK/US approval rates worldwide. Most students walk in without rehearsing a single answer.",
  },
  {
    icon: <Coins className="size-6" strokeWidth={1.5} />,
    title: "Consultants cost a semester.",
    body: "A typical Lahore agency asks PKR 40,000–150,000 for a templated SOP and the same six universities they give everyone.",
  },
  {
    icon: <FileSignature className="size-6" strokeWidth={1.5} />,
    title: "SOPs that read like everyone else's.",
    body: "Generic essays lose at the first read. Your statement has to ground in Pakistan and name the scholarship by what it actually funds.",
  },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-ivory">
      {/* ─── LandingNav (§3.2). Sticky after 80px scroll handled by Tailwind sticky. ─── */}
      <header className="sticky top-0 z-30 border-b border-[var(--color-border-quiet)] bg-ivory/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1200px] items-center justify-between px-6 py-4 md:px-16 md:py-5">
          <Link
            href="/"
            className="font-display text-[22px] italic font-[450] tracking-[-0.02em] text-ink-deep"
          >
            {BRAND_DISPLAY_NAME}
          </Link>
          <nav className="flex items-center gap-1 md:gap-2" aria-label="Primary">
            <Button asChild variant="ghost" size="sm" className="hidden md:inline-flex">
              <Link href="#how">How it works</Link>
            </Button>
            <Button asChild variant="ghost" size="sm" className="hidden md:inline-flex">
              <Link href="#scholarships">Scholarships</Link>
            </Button>
            <Button asChild variant="ghost" size="sm">
              <Link href="/upgrade">Pricing</Link>
            </Button>
            <Button asChild variant="ghost" size="sm">
              <Link href="/login">Sign in</Link>
            </Button>
            <Button asChild size="sm">
              <Link href="/signup">Get started</Link>
            </Button>
          </nav>
        </div>
      </header>

      <main id="main">
        {/* ─── §6.1 Hero ─── */}
        <section className="border-b border-[var(--color-border-quiet)]">
          <div className="mx-auto grid max-w-[1200px] gap-12 px-6 pt-16 pb-20 md:px-16 md:pt-28 md:pb-28 lg:grid-cols-12 lg:items-center lg:gap-16">
            <div className="lg:col-span-7">
              <p className="font-mono text-[11px] uppercase tracking-[0.12em] text-lapis">
                For Pakistani applicants · UK · US · Canada · Germany · Australia
              </p>
              <h1 className="mt-6 max-w-[16ch] font-display text-[44px] italic font-[400] leading-[1.05] tracking-[-0.02em] text-ink-deep md:text-[64px] md:leading-[1.02]">
                Funded <RotatingDegree /> degrees, found for you.
              </h1>
              <p className="mt-6 max-w-[60ch] text-[17px] leading-[1.55] text-ink-muted md:text-[19px]">
                {BRAND_DISPLAY_NAME} matches Pakistani students with fully-funded
                scholarships in the UK, US, Canada, Germany, and Australia. We
                ground every match in your CGPA, target field, and household
                context — no consultant required.
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <Button asChild size="lg">
                  <Link href="/signup">
                    Get started — free <ArrowRight className="size-4" strokeWidth={1.5} />
                  </Link>
                </Button>
                <Button asChild variant="secondary" size="lg">
                  <Link href="#how">See how it works</Link>
                </Button>
              </div>
              <p className="mt-4 font-mono text-[12px] text-ink-subtle">
                No payment required · PDPB-aligned · 90-second signup
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <StatChip value="47" label="universities" />
                <StatChip value="20" label="scholarships live" />
                <StatChip value="70" label="visa questions" />
              </div>
            </div>

            {/* Editorial preview — visible at lg+. Shows real provider output
                so the hero anchors visually without a stock illustration. */}
            <aside
              aria-hidden
              className="hidden lg:col-span-5 lg:block"
            >
              <div className="rounded-[28px] border border-[var(--color-border)] bg-paper-warm p-7">
                <div className="flex items-center justify-between">
                  <p className="font-mono text-[11px] uppercase tracking-[0.08em] text-lapis">
                    Live this week
                  </p>
                  <Badge tone="validated">3 new</Badge>
                </div>
                <ul className="mt-6 divide-y divide-[var(--color-border-quiet)]">
                  {PROVIDERS.slice(0, 3).map((p) => (
                    <li key={p.name} className="py-4 first:pt-0 last:pb-0">
                      <div className="flex items-baseline justify-between gap-3">
                        <p className="font-display text-[20px] italic font-[450] text-ink-deep">
                          {p.name}
                        </p>
                        <p className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
                          {p.country}
                        </p>
                      </div>
                      <p className="mt-1.5 text-[13px] leading-[1.5] text-ink-muted">{p.funding}</p>
                    </li>
                  ))}
                </ul>
                <div className="mt-6 flex items-center justify-between border-t border-[var(--color-border-quiet)] pt-4">
                  <p className="font-mono text-[11px] text-ink-subtle">
                    Updated 2026-05-18
                  </p>
                  <Link
                    href="/discover"
                    className="font-mono text-[11px] uppercase tracking-[0.06em] text-lapis underline-offset-2 hover:underline"
                  >
                    See 17 more →
                  </Link>
                </div>
              </div>
            </aside>
          </div>
        </section>

        {/* ─── §6.1 Problem section ─── */}
        <section className="border-b border-[var(--color-border-quiet)] bg-paper-warm/40">
          <div className="mx-auto max-w-[1200px] px-6 py-20 md:px-16 md:py-24">
            <div className="grid gap-12 md:grid-cols-12 md:items-end">
              <div className="md:col-span-5">
                <CardEyebrow className="text-lapis">The Pakistani applicant tax</CardEyebrow>
                <h2 className="mt-3 font-display text-[32px] leading-[1.2] tracking-[-0.02em] text-ink-deep md:text-[40px]">
                  Three things between you and a funded place.
                </h2>
                <p className="mt-4 max-w-prose text-[15px] text-ink-muted">
                  Most students lose to friction, not talent. {BRAND_DISPLAY_NAME}
                  collapses the three places Pakistani applicants actually drop off.
                </p>
              </div>
              <ul role="list" className="grid gap-4 md:col-span-7">
                {PROBLEMS.map((p, i) => (
                  <li key={p.title}>
                    <Card className="p-5 md:p-6">
                      <div className="flex gap-4">
                        <span
                          aria-hidden
                          className="flex size-11 shrink-0 items-center justify-center rounded-[10px] bg-paper-warm text-ink-deep"
                        >
                          {p.icon}
                        </span>
                        <div>
                          <p className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
                            {String(i + 1).padStart(2, "0")}
                          </p>
                          <h3 className="mt-1 text-[17px] font-semibold leading-tight text-ink-deep">
                            {p.title}
                          </h3>
                          <p className="mt-2 text-[14px] leading-[1.55] text-ink-muted">{p.body}</p>
                        </div>
                      </div>
                    </Card>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* ─── §6.1 How it works — 4 numbered steps horizontal ─── */}
        <section id="how" className="border-b border-[var(--color-border-quiet)]">
          <div className="mx-auto max-w-[1200px] px-6 py-20 md:px-16 md:py-24">
            <CardEyebrow className="text-lapis">How {BRAND_DISPLAY_NAME.toLowerCase()} works</CardEyebrow>
            <h2 className="mt-3 font-display text-[32px] leading-[1.2] tracking-[-0.02em] text-ink-deep md:text-[40px]">
              Four steps. From profile to visa rehearsal.
            </h2>
            <ol className="mt-12 grid gap-px overflow-hidden rounded-[22px] border border-[var(--color-border)] bg-[var(--color-border)] md:grid-cols-4">
              {STEPS.map((s) => (
                <li key={s.n} className="bg-paper-white p-6 md:p-7">
                  <p className="font-mono text-[28px] tabular-nums leading-none text-lapis">{s.n}</p>
                  <h3 className="mt-5 text-[17px] font-semibold leading-tight text-ink-deep">
                    {s.title}
                  </h3>
                  <p className="mt-2 text-[14px] leading-[1.55] text-ink-muted">{s.body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* ─── §6.1 Featured scholarships ─── */}
        <section id="scholarships" className="border-b border-[var(--color-border-quiet)] bg-paper-warm/40">
          <div className="mx-auto max-w-[1200px] px-6 py-20 md:px-16 md:py-24">
            <div className="flex items-end justify-between gap-6">
              <div>
                <CardEyebrow className="text-lapis">Live scholarships</CardEyebrow>
                <h2 className="mt-3 font-display text-[32px] leading-[1.2] tracking-[-0.02em] text-ink-deep md:text-[40px]">
                  Real, fully-funded, Pakistani-eligible.
                </h2>
              </div>
              <Button asChild variant="link" className="hidden md:inline-flex">
                <Link href="/discover">
                  Browse all → <ArrowRight className="ml-1 size-3.5" strokeWidth={1.5} />
                </Link>
              </Button>
            </div>
            <ul
              role="list"
              className="mt-10 grid gap-px overflow-hidden rounded-[22px] border border-[var(--color-border)] bg-[var(--color-border)] md:grid-cols-2 lg:grid-cols-3"
            >
              {PROVIDERS.map((p) => (
                <li
                  key={p.name}
                  className="group bg-paper-white p-6 transition-colors duration-[var(--motion-micro)] ease-[var(--ease-out)] hover:bg-paper-warm/40"
                >
                  <div className="flex items-start justify-between">
                    <h3 className="text-[20px] font-display italic font-[450] leading-tight text-ink-deep">
                      {p.name}
                    </h3>
                    <Badge tone="validated">Live</Badge>
                  </div>
                  <p className="mt-1 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
                    {p.country}
                  </p>
                  <p className="mt-4 text-[14px] leading-[1.55] text-ink-muted">{p.funding}</p>
                </li>
              ))}
            </ul>
            <Button asChild variant="link" className="mt-6 md:hidden">
              <Link href="/discover">Browse all scholarships →</Link>
            </Button>
          </div>
        </section>

        {/* ─── §6.1 Visa interview callout ─── */}
        <section className="border-b border-[var(--color-border-quiet)]">
          <div className="mx-auto grid max-w-[1200px] items-center gap-12 px-6 py-20 md:grid-cols-12 md:gap-16 md:px-16 md:py-24">
            <div className="md:col-span-5">
              <div className="aspect-[5/6] rounded-[28px] border border-[var(--color-border)] bg-paper-warm p-8">
                <div className="flex h-full flex-col justify-between">
                  <div className="flex items-center gap-2">
                    <Plane className="size-5 text-ink-deep" strokeWidth={1.5} />
                    <p className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-deep">
                      Visa simulator
                    </p>
                  </div>
                  <div>
                    <p className="font-display text-[28px] italic font-[400] leading-[1.1] text-ink-deep">
                      &ldquo;Why this university, and why now?&rdquo;
                    </p>
                    <p className="mt-4 font-mono text-[12px] text-ink-muted">
                      Q14 · UK · Genuine Student
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="size-4 text-validated" strokeWidth={1.5} />
                    <p className="text-[13px] text-ink-muted">Rubric scored · ties to Pakistan</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="md:col-span-7">
              <CardEyebrow className="text-lapis">Practise before the embassy does</CardEyebrow>
              <h2 className="mt-3 font-display text-[32px] leading-[1.2] tracking-[-0.02em] text-ink-deep md:text-[40px]">
                Seventy questions. Four countries. One rubric.
              </h2>
              <p className="mt-5 text-[16px] leading-[1.55] text-ink-muted">
                The visa officer at the UK High Commission asks specific things in
                a specific order. We rehearse the genuine-student narrative, the
                financial-context probe, and the return-intent question — country
                by country, in study or exam mode.
              </p>
              <ul className="mt-6 space-y-3 text-[14px] text-ink-muted">
                <li className="flex gap-3">
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-validated" strokeWidth={1.5} />
                  <span>Country-tuned banks for UK, US, Canada, Germany.</span>
                </li>
                <li className="flex gap-3">
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-validated" strokeWidth={1.5} />
                  <span>Study mode: per-question rubric and a model answer to compare.</span>
                </li>
                <li className="flex gap-3">
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-validated" strokeWidth={1.5} />
                  <span>Elite: full transcript download and shareable feedback.</span>
                </li>
              </ul>
              <div className="mt-8">
                <Button asChild variant="secondary" size="md">
                  <Link href="/interviews/visa">
                    Try the simulator <ArrowRight className="size-4" strokeWidth={1.5} />
                  </Link>
                </Button>
              </div>
            </div>
          </div>
        </section>

        {/* ─── FAQ — answer the six questions every signup hesitates on. ─── */}
        <section id="faq" className="border-b border-[var(--color-border-quiet)]">
          <div className="mx-auto grid max-w-[1200px] gap-12 px-6 py-20 md:grid-cols-12 md:gap-16 md:px-16 md:py-24">
            <div className="md:col-span-4">
              <CardEyebrow className="text-lapis">Questions</CardEyebrow>
              <h2 className="mt-3 font-display text-[32px] leading-[1.2] tracking-[-0.02em] text-ink-deep md:text-[40px]">
                The things every applicant asks first.
              </h2>
              <p className="mt-4 max-w-prose text-[15px] text-ink-muted">
                Six honest answers. If something else is on your mind, write to{" "}
                <a
                  href="mailto:support@aidwiseai.pk"
                  className="text-lapis underline underline-offset-2 hover:decoration-2"
                >
                  support@aidwiseai.pk
                </a>
                .
              </p>
            </div>
            <ul role="list" className="md:col-span-8">
              {FAQS.map((f) => (
                <li key={f.q} className="border-b border-[var(--color-border-quiet)] first:border-t">
                  <details className="group [&_summary::-webkit-details-marker]:hidden">
                    <summary className="flex cursor-pointer list-none items-center justify-between gap-6 py-5 text-[16px] font-medium text-ink-deep transition-colors hover:text-lapis md:text-[17px]">
                      {f.q}
                      <Plus
                        className="size-4 shrink-0 text-ink-subtle transition-transform duration-[var(--motion-layout)] ease-[var(--ease-out)] group-open:rotate-45 group-open:text-lapis"
                        strokeWidth={1.5}
                        aria-hidden
                      />
                    </summary>
                    <div className="pb-6 pr-10 text-[15px] leading-[1.65] text-ink-muted">
                      {f.a}
                    </div>
                  </details>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* ─── §6.1 Pricing teaser — 3 PricingCards (Explorer/Pro/Elite) ─── */}
        <section className="border-b border-[var(--color-border-quiet)] bg-paper-warm/40">
          <div className="mx-auto max-w-[1200px] px-6 py-20 md:px-16 md:py-24">
            <div className="text-center">
              <CardEyebrow className="text-lapis">Pricing</CardEyebrow>
              <h2 className="mt-3 font-display text-[32px] leading-[1.2] tracking-[-0.02em] text-ink-deep md:text-[40px]">
                Start free. Upgrade when you&apos;re ready.
              </h2>
            </div>
            <div className="mt-12 grid gap-px overflow-hidden rounded-[22px] border border-[var(--color-border)] bg-[var(--color-border)] md:grid-cols-3">
              <PricingTeaser
                tier="Explorer"
                price="Free"
                period="forever"
                features={[
                  "3 scholarship matches",
                  "1 SOP draft (lifetime)",
                  "3 visa questions (UK only)",
                ]}
                cta="Get started"
                ctaHref="/signup"
              />
              <PricingTeaser
                tier="Pro"
                price="PKR 2,999"
                period="per month"
                italic
                features={[
                  "6 matches updated weekly",
                  "5 SOP drafts per month",
                  "Full visa bank, all four countries",
                ]}
                cta="See pricing"
                ctaHref="/upgrade"
                badge="Recommended"
              />
              <PricingTeaser
                tier="Elite"
                price="PKR 6,000"
                period="per month"
                italic
                features={[
                  "12 matches + provenance trail",
                  "10 SOP drafts + line-by-line feedback",
                  "Transcript download + mentor review",
                ]}
                cta="See pricing"
                ctaHref="/upgrade"
              />
            </div>
            <p className="mt-6 text-center font-mono text-[12px] text-ink-subtle">
              Switch currency on the pricing page. Pay via JazzCash, Easypaisa, or IBAN.
            </p>
          </div>
        </section>

        {/* ─── Closing CTA — the last touchpoint before footer. ─── */}
        <section
          aria-labelledby="cta-close-heading"
          className="border-b border-[var(--color-border-quiet)] bg-ivory"
        >
          <div className="mx-auto max-w-[760px] px-6 py-20 text-center md:py-28">
            <CardEyebrow className="text-lapis">Ninety seconds, free</CardEyebrow>
            <h2
              id="cta-close-heading"
              className="mt-4 font-display text-[36px] italic font-[400] leading-[1.05] tracking-[-0.02em] text-ink-deep md:text-[52px]"
            >
              Start the application your consultant won&apos;t draft.
            </h2>
            <p className="mx-auto mt-5 max-w-[52ch] text-[16px] leading-[1.55] text-ink-muted md:text-[17px]">
              Free forever for one full SOP and three matches. Upgrade only when
              the visa rehearsals start paying off.
            </p>
            <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
              <Button asChild size="lg">
                <Link href="/signup">
                  Create account <ArrowRight className="size-4" strokeWidth={1.5} />
                </Link>
              </Button>
              <Button asChild variant="ghost" size="lg">
                <Link href="/upgrade">See pricing</Link>
              </Button>
            </div>
            <p className="mt-6 font-mono text-[12px] text-ink-subtle">
              No credit card · Email signup · Cancel any time
            </p>
          </div>
        </section>

        {/* ─── §6.1 Footer ─── */}
        <footer className="bg-ink-deep text-paper-white">
          <div className="mx-auto grid max-w-[1200px] gap-12 px-6 py-16 md:grid-cols-12 md:gap-16 md:px-16 md:py-20">
            <div className="md:col-span-4">
              <p className="font-display text-[28px] italic font-[400] tracking-[-0.02em]">
                {BRAND_DISPLAY_NAME}
              </p>
              <p className="mt-3 max-w-[34ch] text-[14px] leading-[1.6] text-paper-white/70">
                {BRAND_DISPLAY_NAME} — built for Pakistani applicants. Pakistan-priced.
                PDPB-aligned. No consultant fees.
              </p>
              <div className="mt-6 flex items-center gap-2 text-[13px] text-paper-white/60">
                <Building2 className="size-4" strokeWidth={1.5} />
                <span>Karachi · Lahore · Islamabad</span>
              </div>
            </div>
            <FooterColumn
              title="Product"
              links={[
                { href: "/discover", label: "Scholarships" },
                { href: "/interviews/visa", label: "Visa simulator" },
                { href: "/upgrade", label: "Pricing" },
                { href: "/universities", label: "Universities" },
              ]}
            />
            <FooterColumn
              title="Trial"
              links={[
                { href: "/booth/air-university", label: "Air University trial" },
                { href: "/signup", label: "Create account" },
                { href: "/login", label: "Sign in" },
              ]}
            />
            <FooterColumn
              title="Legal"
              links={[
                { href: "/legal/terms", label: "Terms" },
                { href: "/legal/privacy", label: "Privacy notice" },
                { href: "/legal/dpa", label: "Data processing" },
                { href: "/legal/cookie", label: "Cookie policy" },
                { href: "/legal/refund", label: "Refund policy" },
              ]}
            />
          </div>
          <div className="border-t border-paper-white/10">
            <div className="mx-auto flex max-w-[1200px] flex-col gap-3 px-6 py-6 text-[12px] text-paper-white/60 md:flex-row md:items-center md:justify-between md:px-16">
              <p className="font-mono">
                © {new Date().getFullYear()} {BRAND_DISPLAY_NAME}. All rights reserved.
              </p>
              <p className="flex items-center gap-2 font-mono">
                <CalendarRange className="size-3.5" strokeWidth={1.5} />
                <span>Updated 2026-05-17</span>
              </p>
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
}

function PricingTeaser({
  tier,
  price,
  period,
  features,
  cta,
  ctaHref,
  italic,
  badge,
}: {
  tier: string;
  price: string;
  period: string;
  features: string[];
  cta: string;
  ctaHref: string;
  italic?: boolean;
  badge?: string;
}) {
  return (
    <div className="flex flex-col bg-paper-white p-6 md:p-8">
      <div className="flex items-center justify-between">
        <h3
          className={`font-display text-[24px] leading-tight text-ink-deep ${
            italic ? "italic font-[450]" : "font-[500]"
          }`}
        >
          {tier}
        </h3>
        {badge ? <Badge tone="lapis">{badge}</Badge> : null}
      </div>
      <div className="mt-4 flex items-baseline gap-2">
        <span className="font-mono text-[28px] font-semibold tabular-nums text-ink-deep">
          {price}
        </span>
        <span className="text-[13px] text-ink-subtle">{period}</span>
      </div>
      <ul className="mt-6 space-y-2.5 text-[14px] text-ink-muted">
        {features.map((f) => (
          <li key={f} className="flex gap-2.5">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-validated" strokeWidth={1.5} />
            <span>{f}</span>
          </li>
        ))}
      </ul>
      <Button asChild variant="secondary" size="md" className="mt-8 w-full">
        <Link href={ctaHref}>{cta}</Link>
      </Button>
    </div>
  );
}

function FooterColumn({
  title,
  links,
}: {
  title: string;
  links: { href: string; label: string }[];
}) {
  return (
    <div className="md:col-span-2 lg:col-span-2 xl:col-span-2">
      <p className="font-mono text-[11px] uppercase tracking-[0.08em] text-paper-white/50">
        {title}
      </p>
      <ul className="mt-4 space-y-2.5 text-[14px]">
        {links.map((l) => (
          <li key={l.href}>
            <Link
              href={l.href}
              className="text-paper-white/85 transition-colors duration-[var(--motion-micro)] hover:text-paper-white"
            >
              {l.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
