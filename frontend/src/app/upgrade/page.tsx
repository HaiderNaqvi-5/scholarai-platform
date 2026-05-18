"use client";

/**
 * /upgrade — Pricing (Front-upgrade §6.3).
 *
 * 4-tier cards (Explorer / Pro / Elite / Institution), currency switcher
 * across the five supported currencies, comparison table, and a waitlist
 * accordion within each card (no Stripe — payment is post-FYP).
 * Institution CTA is a mailto.
 *
 * Per-screen bans: "Most popular" badge with gradient ribbon, "Save 20%!"
 * strikethrough red, faux-3D card, "Best value" auto-highlight without
 * explanation. Allowed: a neutral "Recommended" chip with a one-line
 * reason; named features ("5 SOP drafts per month").
 */

import Link from "next/link";
import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Check, Mail, ChevronDown, Plus, Minus, Globe2 } from "lucide-react";
import { toast } from "sonner";

import { ApiError, endpoints } from "@/lib/api";
import type { Currency, Plan, PricingTier } from "@/lib/api";
import { useAuth } from "@/lib/auth/AuthProvider";
import { Button } from "@/components/ui/button";
import { Card, CardEyebrow } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton, SkeletonCard } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ErrorState } from "@/components/ui/states";
import { cn } from "@/lib/utils";

import { partnershipsMailto, BRAND_DISPLAY_NAME } from "@/lib/brand";
import { useGeoCurrency } from "@/lib/geo/useGeoCurrency";

const CURRENCIES: Currency[] = ["PKR", "GBP", "EUR", "AED", "USD"];
const INSTITUTION_MAILTO = partnershipsMailto("Institution Partnership Inquiry");

export default function UpgradePage() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <UpgradeInner />
    </Suspense>
  );
}

function UpgradeInner() {
  const auth = useAuth();
  const params = useSearchParams();
  const queryPlan = (params.get("plan") || "").toLowerCase();
  const queryCurrency = (params.get("currency") || "").toUpperCase() as Currency | "";

  const authedCurrency: Currency | null =
    auth.status === "authed" && auth.user.plan_currency &&
    CURRENCIES.includes(auth.user.plan_currency)
      ? auth.user.plan_currency
      : null;

  const geo = useGeoCurrency(authedCurrency ?? "PKR");
  const [fallbackOverride, setFallbackOverride] = useState<Currency | null>(null);

  const queryOverride: Currency | null =
    CURRENCIES.includes(queryCurrency as Currency) && queryCurrency !== ""
      ? (queryCurrency as Currency)
      : null;

  const currency: Currency =
    fallbackOverride ?? queryOverride ?? authedCurrency ?? geo.currency;

  const detectionLabel: string =
    queryOverride !== null
      ? "Shared link override"
      : fallbackOverride !== null
        ? "Manual selection"
        : authedCurrency !== null
          ? "Your billing currency"
          : geo.source === "geo" || geo.source === "cache"
            ? geo.country
              ? `Detected from ${geo.country}`
              : "Detected from your location"
            : "Default for Pakistan";

  const pricingQ = useQuery({
    queryKey: ["upgrade", "pricing", currency],
    queryFn: () => endpoints.upgrade.pricing(currency),
    staleTime: 5 * 60_000,
  });

  const currentPlan: Plan | null = auth.status === "authed" ? auth.user.plan : null;

  return (
    <div className="min-h-screen bg-ivory">
      <Header />
      <main id="main" className="mx-auto max-w-[1200px] px-6 pb-24 pt-12 md:px-12 md:pt-20">
        <Hero />

        <DetectedCurrency currency={currency} label={detectionLabel} />

        {pricingQ.isLoading ? <PageSkeleton /> : null}

        {pricingQ.isError ? (
          <div className="mt-12">
            <ErrorState
              title="Couldn't load pricing."
              description="Live currency rates are unavailable right now. Try again or default to PKR."
              action={
                <>
                  <Button variant="secondary" onClick={() => pricingQ.refetch()}>
                    Retry
                  </Button>
                  <Button variant="ghost" onClick={() => setFallbackOverride("PKR")}>
                    Show in PKR
                  </Button>
                </>
              }
            />
          </div>
        ) : null}

        {pricingQ.data ? (
          <>
            <PricingGrid
              tiers={pricingQ.data.tiers}
              currentPlan={currentPlan}
              focusedPlan={queryPlan || null}
              currency={currency}
            />
            <ComparisonTable tiers={pricingQ.data.tiers} />
            <Faq />
          </>
        ) : null}

        <PartnerFooter />
      </main>
    </div>
  );
}

// ───────────────────────────────────────────────────────────────────────────
// Header / Hero
// ───────────────────────────────────────────────────────────────────────────

function Header() {
  return (
    <header className="sticky top-0 z-30 border-b border-[var(--color-border-quiet)] bg-ivory/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-[1200px] items-center justify-between px-6 py-4 md:px-12">
        <Link
          href="/"
          className="font-display text-[22px] italic font-[450] tracking-[-0.02em] text-ink-deep"
        >
          {BRAND_DISPLAY_NAME}
        </Link>
        <Link
          href="/feed"
          className="text-[13px] text-ink-muted transition-colors hover:text-ink-deep"
        >
          Back to dashboard →
        </Link>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="text-center">
      <CardEyebrow>Pricing</CardEyebrow>
      <h1 className="mt-3 mx-auto max-w-[18ch] font-display text-[40px] italic font-[400] leading-[1.1] tracking-[-0.02em] text-ink-deep md:text-[52px]">
        Pakistan-priced. Pay in PKR or your local currency.
      </h1>
      <p className="mx-auto mt-5 max-w-[60ch] text-[16px] leading-[1.55] text-ink-muted">
        {BRAND_DISPLAY_NAME} is free to try. When the matching, SOP drafts, and
        visa practice become indispensable, Pro and Elite remove the limits.
      </p>
    </section>
  );
}

function DetectedCurrency({
  currency,
  label,
}: {
  currency: Currency;
  label: string;
}) {
  return (
    <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
      <div
        role="status"
        aria-live="polite"
        className="inline-flex items-center gap-2.5 rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3.5 py-2"
      >
        <Globe2 className="size-4 text-lapis" strokeWidth={1.5} aria-hidden />
        <span className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
          {label}
        </span>
        <span className="h-4 w-px bg-[var(--color-border-quiet)]" aria-hidden />
        <span className="font-mono text-[13px] font-medium tabular-nums text-ink-deep">
          {currency}
        </span>
      </div>
    </div>
  );
}

// ───────────────────────────────────────────────────────────────────────────
// Pricing grid
// ───────────────────────────────────────────────────────────────────────────

function PricingGrid({
  tiers,
  currentPlan,
  focusedPlan,
  currency,
}: {
  tiers: PricingTier[];
  currentPlan: Plan | null;
  focusedPlan: string | null;
  currency: Currency;
}) {
  return (
    <section className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-4" aria-label="Plan options">
      {tiers.map((plan) => (
        <PricingCard
          key={plan.key}
          plan={plan}
          isCurrent={currentPlan === (plan.key as Plan)}
          isFocused={focusedPlan === plan.key}
          currency={currency}
        />
      ))}
    </section>
  );
}

function PricingCard({
  plan,
  isCurrent,
  isFocused,
  currency,
}: {
  plan: PricingTier;
  isCurrent: boolean;
  isFocused: boolean;
  currency: Currency;
}) {
  const isInstitution = plan.key === "institution";
  const isPaid = plan.key === "pro" || plan.key === "elite";
  const [waitlistOpen, setWaitlistOpen] = useState(false);

  return (
    <Card
      asPanel
      className={cn(
        "relative flex h-full flex-col",
        plan.is_recommended && "ring-1 ring-lapis/30",
        isFocused && "ring-2 ring-[var(--color-ring)] ring-offset-2 ring-offset-ivory",
      )}
      aria-labelledby={`tier-${plan.key}`}
    >
      <div className="flex items-center justify-between">
        <h2
          id={`tier-${plan.key}`}
          className={cn(
            "font-display text-[22px] leading-tight text-ink-deep",
            plan.key === "explorer" ? "font-[500]" : "italic font-[450]",
          )}
        >
          {plan.label}
        </h2>
        {plan.is_recommended ? <Badge tone="lapis">Recommended</Badge> : null}
        {isCurrent ? <Badge tone="validated">Current</Badge> : null}
      </div>

      <div className="mt-5">
        <p className="price-fade font-mono text-[28px] font-semibold leading-none tabular-nums text-ink-deep" key={`${plan.key}-${currency}`}>
          {plan.monthly_price}
        </p>
        {plan.yearly_hint ? (
          <p className="mt-2 text-[12px] text-ink-subtle">{plan.yearly_hint}</p>
        ) : null}
      </div>

      <p className="mt-4 text-[14px] leading-[1.55] text-ink-muted">{plan.feature_summary}</p>

      <ul className="mt-5 flex-1 space-y-2.5 border-t border-[var(--color-border-quiet)] pt-5">
        {plan.bullet_features.map((bullet) => (
          <li key={bullet} className="flex gap-2.5 text-[14px] leading-[1.5] text-ink-deep">
            <Check className="mt-0.5 size-4 shrink-0 text-validated" strokeWidth={1.75} aria-hidden />
            <span>{bullet}</span>
          </li>
        ))}
      </ul>

      <div className="mt-6">
        {isInstitution ? (
          <Button asChild variant="secondary" className="w-full">
            <a href={INSTITUTION_MAILTO}>
              <Mail className="size-4" strokeWidth={1.5} aria-hidden />
              Email partnerships
            </a>
          </Button>
        ) : plan.key === "explorer" ? (
          <Button asChild variant="secondary" className="w-full">
            <Link href={isCurrent ? "/feed" : "/signup"}>
              {isCurrent ? "Your current plan" : "Get started"}
            </Link>
          </Button>
        ) : (
          <>
            <Button
              type="button"
              variant={plan.is_recommended ? "lapis" : "secondary"}
              className="w-full"
              onClick={() => setWaitlistOpen((o) => !o)}
              aria-expanded={waitlistOpen}
              aria-controls={`waitlist-${plan.key}`}
            >
              {isCurrent ? "Your current plan" : `Join ${plan.label} waitlist`}
              <ChevronDown
                className={cn(
                  "size-4 transition-transform duration-[var(--motion-micro)]",
                  waitlistOpen && "rotate-180",
                )}
                strokeWidth={1.5}
              />
            </Button>
            {waitlistOpen ? (
              <WaitlistAccordion
                planKey={plan.key as "pro" | "elite"}
                planLabel={plan.label}
                currency={currency}
                onClose={() => setWaitlistOpen(false)}
              />
            ) : null}
          </>
        )}
      </div>

      {isPaid ? (
        <p className="mt-3 text-center font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
          No card required
        </p>
      ) : null}
    </Card>
  );
}

// ───────────────────────────────────────────────────────────────────────────
// Waitlist accordion (within card, never modal)
// ───────────────────────────────────────────────────────────────────────────

function WaitlistAccordion({
  planKey,
  planLabel,
  currency,
  onClose,
}: {
  planKey: "pro" | "elite";
  planLabel: string;
  currency: Currency;
  onClose: () => void;
}) {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const join = useMutation({
    mutationFn: () => endpoints.upgrade.joinWaitlist({ email, plan: planKey, currency }),
    onSuccess: () => {
      setSubmitted(true);
      toast.success("On the waitlist — we'll email you when payment opens.");
    },
    onError: (err) => {
      const msg = err instanceof ApiError ? err.message : "Couldn't join the waitlist.";
      toast.error(msg);
    },
  });

  if (submitted) {
    return (
      <div
        id={`waitlist-${planKey}`}
        className="mt-4 rounded-[10px] border border-validated/30 bg-validated-soft px-4 py-3"
        role="status"
      >
        <p className="text-[13px] leading-[1.5] text-validated">
          You&apos;re on the {planLabel} waitlist. We&apos;ll email <span className="font-mono">{email}</span>{" "}
          when payment opens.
        </p>
      </div>
    );
  }

  return (
    <form
      id={`waitlist-${planKey}`}
      onSubmit={(e) => {
        e.preventDefault();
        if (email) join.mutate();
      }}
      className="mt-4 space-y-2.5"
    >
      <Label htmlFor={`waitlist-${planKey}-email`} className="text-[12px]">
        Email for early access
      </Label>
      <Input
        id={`waitlist-${planKey}-email`}
        type="email"
        required
        placeholder="you@example.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        autoComplete="email"
      />
      <div className="flex gap-2">
        <Button type="submit" loading={join.isPending} size="sm" className="flex-1">
          Reserve my spot
        </Button>
        <Button type="button" variant="ghost" size="sm" onClick={onClose}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

// ───────────────────────────────────────────────────────────────────────────
// Comparison table
// ───────────────────────────────────────────────────────────────────────────

type TierKey = "explorer" | "pro" | "elite" | "institution";

const COMPARISON_ROWS: { label: string; values: Record<TierKey, string> }[] = [
  {
    label: "Scholarship matches",
    values: { explorer: "3 sample", pro: "6 personalised", elite: "12 with provenance", institution: "Bulk" },
  },
  { label: "University matches", values: { explorer: "—", pro: "6", elite: "12", institution: "Unlimited" } },
  { label: "Application tracker", values: { explorer: "3 cards", pro: "6 cards", elite: "12 cards", institution: "Unlimited" } },
  {
    label: "SOP drafts",
    values: { explorer: "1 lifetime", pro: "5 / month", elite: "10 / month", institution: "50 / seat" },
  },
  { label: "SOP line-by-line feedback", values: { explorer: "—", pro: "—", elite: "Included", institution: "Included" } },
  {
    label: "Visa interview",
    values: { explorer: "Q1–Q3", pro: "Full 10 questions", elite: "Full + downloadable transcript", institution: "Full" },
  },
  {
    label: "Deadline alerts",
    values: {
      explorer: "Email (30 days)",
      pro: "Email always-on",
      elite: "Email + WhatsApp",
      institution: "Email + WhatsApp",
    },
  },
  { label: "Professor email generator", values: { explorer: "—", pro: "—", elite: "Included", institution: "Included" } },
  { label: "Strategy report (PDF)", values: { explorer: "—", pro: "—", elite: "Included", institution: "Included" } },
];

function ComparisonTable({ tiers }: { tiers: PricingTier[] }) {
  return (
    <section className="mt-20">
      <h2 className="font-display text-[24px] italic font-[450] leading-tight text-ink-deep">
        What you get at each tier
      </h2>
      <div className="mt-6 overflow-x-auto rounded-[18px] border border-[var(--color-border)] bg-paper-white">
        <table className="w-full min-w-[720px] border-collapse">
          <caption className="sr-only">Feature comparison across Explorer, Pro, Elite, and Institution plans</caption>
          <thead className="border-b border-[var(--color-border-quiet)] bg-paper-warm/40">
            <tr className="text-left">
              <th scope="col" className="px-5 py-4 text-[11px] font-mono uppercase tracking-[0.06em] text-ink-subtle">
                Feature
              </th>
              {tiers.map((t) => (
                <th
                  key={t.key}
                  scope="col"
                  className="px-4 py-4 font-display text-[15px] font-semibold text-ink-deep"
                >
                  {t.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {COMPARISON_ROWS.map((row) => (
              <tr
                key={row.label}
                className="border-b border-[var(--color-border-quiet)] last:border-b-0 hover:bg-paper-warm/30"
              >
                <th scope="row" className="px-5 py-3.5 text-left text-[14px] font-medium text-ink-deep">
                  {row.label}
                </th>
                {tiers.map((t) => (
                  <td key={t.key} className="px-4 py-3.5 text-[14px] text-ink-muted">
                    {row.values[t.key as TierKey] ?? "—"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

// ───────────────────────────────────────────────────────────────────────────
// FAQ
// ───────────────────────────────────────────────────────────────────────────

const FAQ_ITEMS: { q: string; a: string }[] = [
  {
    q: "When does payment go live?",
    a: "After the FYP cohort completes its trial. Until then, joining the waitlist reserves your spot — you'll be billed only after you confirm payment method.",
  },
  {
    q: "How does the Air University trial work?",
    a: `Use code AIRU2026 at signup before May 26, 23:59 PKT. You get 30 days of Pro free — every match, every SOP draft, every visa question. No card required.`,
  },
  {
    q: "Can I switch plans later?",
    a: "Yes. Pro and Elite are month-to-month. Downgrading takes effect at the next billing cycle; we don't pro-rate.",
  },
  {
    q: "Which currencies do you accept?",
    a: "PKR, GBP, EUR, AED, USD. Switch the toggle above the cards. Pricing is anchored in PKR — non-PKR values are converted at the current bank rate.",
  },
  {
    q: "What's the refund policy?",
    a: "7-day refund on any first-time monthly purchase. See the refund policy in our legal docs for the exact terms.",
  },
  {
    q: "Do you share my data with universities?",
    a: "Only with explicit opt-in (Pro+) and only with institutions that have signed a DPA. We snapshot once at share time — never retro-leak.",
  },
];

function Faq() {
  const [openId, setOpenId] = useState<number | null>(null);

  return (
    <section className="mt-20">
      <h2 className="font-display text-[24px] italic font-[450] leading-tight text-ink-deep">
        Questions
      </h2>
      <ul className="mt-6 divide-y divide-[var(--color-border-quiet)] rounded-[18px] border border-[var(--color-border)] bg-paper-white">
        {FAQ_ITEMS.map((item, i) => {
          const open = openId === i;
          return (
            <li key={item.q}>
              <button
                type="button"
                onClick={() => setOpenId(open ? null : i)}
                aria-expanded={open}
                aria-controls={`faq-panel-${i}`}
                className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left transition-colors hover:bg-paper-warm/30 tap-target"
              >
                <span className="text-[15px] font-medium text-ink-deep">{item.q}</span>
                {open ? (
                  <Minus className="size-4 shrink-0 text-ink-muted" strokeWidth={1.5} />
                ) : (
                  <Plus className="size-4 shrink-0 text-ink-muted" strokeWidth={1.5} />
                )}
              </button>
              {open ? (
                <p
                  id={`faq-panel-${i}`}
                  className="px-5 pb-4 text-[14px] leading-[1.6] text-ink-muted"
                >
                  {item.a}
                </p>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

function PartnerFooter() {
  return (
    <footer className="mt-20 border-t border-[var(--color-border-quiet)] pt-8 text-center">
      <p className="text-[14px] text-ink-muted">
        Are you a university or Pakistani school?{" "}
        <Link
          href="/universities"
          className="text-lapis underline decoration-1 underline-offset-2 hover:decoration-2"
        >
          Partner with us →
        </Link>
      </p>
      <p className="mt-2 font-mono text-[12px] text-ink-subtle">
        Questions? <a className="underline underline-offset-2" href={INSTITUTION_MAILTO}>partnerships@scholarai.pk</a>
      </p>
    </footer>
  );
}

// ───────────────────────────────────────────────────────────────────────────
// Skeleton
// ───────────────────────────────────────────────────────────────────────────

function PageSkeleton() {
  return (
    <div className="mt-12">
      <div className="mb-4 flex justify-center">
        <Skeleton className="h-9 w-72 rounded-[12px]" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} className="h-[420px]" />
        ))}
      </div>
    </div>
  );
}
