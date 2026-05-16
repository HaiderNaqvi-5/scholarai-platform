"use client";

/**
 * /upgrade — Pakistan-pivot pricing page (PRD §0.5).
 *
 * 4-tier cards (Explorer / Pro / Elite / Institution), currency switcher across
 * the five supported currencies, comparison table, and a waitlist form
 * (no Stripe — payment is post-FYP). Institution CTA is a mailto.
 */

import Link from "next/link";
import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Check, Mail, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { ApiError, endpoints } from "@/lib/api";
import type { Currency, Plan, PricingTier } from "@/lib/api";
import { useAuth } from "@/lib/auth/AuthProvider";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

import { partnershipsMailto } from "@/lib/brand";
import { defaultCurrencyForCountry } from "@/lib/countries";

const CURRENCIES: Currency[] = ["PKR", "GBP", "EUR", "AED", "USD"];
const INSTITUTION_MAILTO = partnershipsMailto("Institution Partnership Inquiry");

function defaultCurrencyFor(
  user: { billing_country?: string | null; plan_currency?: Currency } | null,
): Currency {
  return user?.plan_currency ?? defaultCurrencyForCountry(user?.billing_country);
}

export default function UpgradePage() {
  return (
    <Suspense fallback={<UpgradeSkeleton />}>
      <UpgradeInner />
    </Suspense>
  );
}

function UpgradeInner() {
  const auth = useAuth();
  const params = useSearchParams();
  const queryPlan = (params.get("plan") || "").toLowerCase();
  const queryCurrency = (params.get("currency") || "").toUpperCase() as Currency | "";

  const initialCurrency: Currency =
    CURRENCIES.includes(queryCurrency as Currency) && queryCurrency !== ""
      ? (queryCurrency as Currency)
      : defaultCurrencyFor(auth.status === "authed" ? auth.user : null);

  const [currency, setCurrency] = useState<Currency>(initialCurrency);
  // No effect-driven re-sync to auth: the URL pins currency when supplied and
  // the lazy initial honours user.plan_currency at first paint. Manual switch
  // via <CurrencySwitcher /> is the only post-mount path.

  const pricingQ = useQuery({
    queryKey: ["upgrade", "pricing", currency],
    queryFn: () => endpoints.upgrade.pricing(currency),
    staleTime: 5 * 60_000,
  });

  const currentPlan: Plan | null = auth.status === "authed" ? auth.user.plan : null;

  return (
    <div className="min-h-screen bg-paper">
      <Header />
      <main className="mx-auto max-w-6xl px-4 pb-20 pt-10 md:pt-16">
        <Hero />

        <CurrencySwitcher current={currency} onChange={setCurrency} />

        {pricingQ.isLoading && <UpgradeSkeleton />}

        {pricingQ.isError && (
          <ErrorBlock onRetry={() => pricingQ.refetch()} message="Couldn't load pricing." />
        )}

        {pricingQ.data && (
          <>
            <PricingGrid
              tiers={pricingQ.data.tiers}
              currentPlan={currentPlan}
              focusedPlan={queryPlan || null}
            />
            <ComparisonTable tiers={pricingQ.data.tiers} />
            <WaitlistSection
              currency={currency}
              defaultPlan={(queryPlan === "elite" ? "elite" : "pro") as "pro" | "elite"}
            />
          </>
        )}

        <PartnerFooter />
      </main>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sections
// ---------------------------------------------------------------------------

function Header() {
  return (
    <header className="border-b border-[var(--color-border)] bg-paper-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <Link href="/" className="font-display text-lg text-ink">
          AidwiseAI
        </Link>
        <Link href="/feed" className="text-sm text-ink-muted hover:text-ink">
          Back to dashboard →
        </Link>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="text-center">
      <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">
        Pricing
      </p>
      <h1 className="mt-2 font-display text-3xl text-ink md:text-4xl">
        Less than one consultant meeting. Every month.
      </h1>
      <p className="mx-auto mt-3 max-w-2xl text-ink-muted">
        AidwiseAI is free to try. When the matching, SOP drafts, and visa
        practice become indispensable, Pro and Elite remove the limits.
      </p>
    </section>
  );
}

function CurrencySwitcher({
  current,
  onChange,
}: {
  current: Currency;
  onChange: (c: Currency) => void;
}) {
  return (
    <div className="mt-8 flex flex-wrap items-center justify-center gap-2">
      <span className="font-mono text-xs uppercase tracking-wide text-ink-muted">
        Show prices in
      </span>
      <div className="inline-flex rounded-[12px] border border-[var(--color-border)] bg-paper-white p-1">
        {CURRENCIES.map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => onChange(c)}
            aria-pressed={current === c}
            className={cn(
              "h-9 min-w-12 rounded-[10px] px-3 text-sm font-medium transition-colors",
              current === c
                ? "bg-ink text-paper"
                : "text-ink-muted hover:bg-paper-warm hover:text-ink",
            )}
          >
            {c}
          </button>
        ))}
      </div>
    </div>
  );
}

function PricingGrid({
  tiers,
  currentPlan,
  focusedPlan,
}: {
  tiers: PricingTier[];
  currentPlan: Plan | null;
  focusedPlan: string | null;
}) {
  return (
    <section className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {tiers.map((plan) => (
        <PricingCard
          key={plan.key}
          plan={plan}
          isCurrent={currentPlan === (plan.key as Plan)}
          isFocused={focusedPlan === plan.key}
        />
      ))}
    </section>
  );
}

function PricingCard({
  plan,
  isCurrent,
  isFocused,
}: {
  plan: PricingTier;
  isCurrent: boolean;
  isFocused: boolean;
}) {
  const isInstitution = plan.key === "institution";
  const cta =
    isInstitution ? (
      <Button asChild variant="secondary" className="w-full">
        <a href={INSTITUTION_MAILTO}>
          <Mail className="size-4" aria-hidden />
          Contact us
        </a>
      </Button>
    ) : plan.key === "explorer" ? (
      <Button asChild variant="secondary" className="w-full">
        <Link href={isCurrent ? "/feed" : "/signup"}>
          {isCurrent ? "Your current plan" : "Start free"}
        </Link>
      </Button>
    ) : (
      <Button asChild className="w-full">
        <a href={`#waitlist-${plan.key}`}>
          {isCurrent ? "Your current plan" : `Choose ${plan.label}`}
        </a>
      </Button>
    );

  return (
    <Card
      className={cn(
        "relative flex h-full flex-col",
        plan.is_recommended && "border-ink/40 shadow-[0_8px_30px_rgba(12,17,23,0.07)]",
        isFocused && "ring-2 ring-[var(--color-ring)] ring-offset-2 ring-offset-paper",
      )}
    >
      {plan.is_recommended && (
        <span className="absolute -top-3 left-5 rounded-full bg-ink px-3 py-1 font-mono text-[10px] uppercase tracking-wide text-paper">
          Most popular
        </span>
      )}
      {plan.key === "elite" && (
        <span className="absolute -top-3 right-5 inline-flex items-center gap-1 rounded-full bg-generated px-3 py-1 font-mono text-[10px] uppercase tracking-wide text-paper-white">
          <Sparkles className="size-3" aria-hidden />
          Serious applicants
        </span>
      )}

      <CardHeader>
        <CardTitle>{plan.label}</CardTitle>
        <p className="text-sm text-ink-muted">{plan.feature_summary}</p>
      </CardHeader>
      <CardBody className="flex flex-1 flex-col gap-4">
        <div>
          <p className="font-display text-2xl text-ink">{plan.monthly_price}</p>
          {plan.yearly_hint && (
            <p className="mt-1 text-xs text-ink-muted">{plan.yearly_hint}</p>
          )}
        </div>
        <ul className="flex-1 space-y-2">
          {plan.bullet_features.map((bullet) => (
            <li key={bullet} className="flex gap-2 text-sm text-ink">
              <Check
                className="mt-0.5 size-4 shrink-0 text-validated"
                aria-hidden
              />
              <span>{bullet}</span>
            </li>
          ))}
        </ul>
      </CardBody>
      <CardFooter>{cta}</CardFooter>
    </Card>
  );
}

// Tier-key union mirrors the backend `_build_tiers` keys (waitlist.py). Typing
// the values map by this union catches drift between the table and the cards
// at compile time — a misspelled "elite" / "explorer" fails build.
type TierKey = "explorer" | "pro" | "elite" | "institution";

const COMPARISON_ROWS: { label: string; values: Record<TierKey, string> }[] = [
  {
    label: "Scholarship matches",
    values: {
      explorer: "3 sample",
      pro: "6 personalised",
      elite: "12 with every match revealed",
      institution: "Bulk",
    },
  },
  {
    label: "University matches",
    values: { explorer: "—", pro: "6", elite: "12", institution: "Unlimited" },
  },
  {
    label: "Application tracker",
    values: { explorer: "3 cards", pro: "6 cards", elite: "12 cards", institution: "Unlimited" },
  },
  {
    label: "SOP drafts",
    values: {
      explorer: "1 lifetime",
      pro: "5 / month",
      elite: "10 / month",
      institution: "50 / seat",
    },
  },
  {
    label: "SOP line-by-line AI",
    values: { explorer: "—", pro: "—", elite: "Included", institution: "Included" },
  },
  {
    label: "Visa interview",
    values: {
      explorer: "Q1–Q3",
      pro: "Full 10 questions",
      elite: "Full + downloadable transcript",
      institution: "Full",
    },
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
  {
    label: "Professor email generator",
    values: { explorer: "—", pro: "—", elite: "Included", institution: "Included" },
  },
  {
    label: "Strategy report (PDF)",
    values: { explorer: "—", pro: "—", elite: "Included", institution: "Included" },
  },
];

function ComparisonTable({ tiers }: { tiers: PricingTier[] }) {
  return (
    <section className="mt-12 overflow-x-auto">
      <h2 className="font-display text-xl text-ink">What&apos;s in each plan</h2>
      <table className="mt-4 w-full min-w-[640px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-[var(--color-border)] text-left">
            <th className="py-3 pr-4 font-medium text-ink-muted">Feature</th>
            {tiers.map((t) => (
              <th key={t.key} className="px-3 py-3 font-display text-ink">
                {t.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {COMPARISON_ROWS.map((row) => (
            <tr
              key={row.label}
              className="border-b border-[var(--color-border)] last:border-b-0"
            >
              <td className="py-3 pr-4 text-ink">{row.label}</td>
              {tiers.map((t) => (
                <td key={t.key} className="px-3 py-3 text-ink-muted">
                  {row.values[t.key as TierKey] ?? "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function WaitlistSection({
  currency,
  defaultPlan,
}: {
  currency: Currency;
  defaultPlan: "pro" | "elite";
}) {
  // Track which defaultPlan we initialised against so a parent change
  // (?plan=elite vs ?plan=pro) re-keys the selection without a setState-in-effect.
  const [planRow, setPlanRow] = useState<{ key: "pro" | "elite"; from: "pro" | "elite" }>(
    { key: defaultPlan, from: defaultPlan },
  );
  if (planRow.from !== defaultPlan) {
    setPlanRow({ key: defaultPlan, from: defaultPlan });
  }
  const plan = planRow.key;
  const setPlan = (next: "pro" | "elite") =>
    setPlanRow({ key: next, from: planRow.from });

  const [email, setEmail] = useState("");

  const join = useMutation({
    mutationFn: () =>
      endpoints.upgrade.joinWaitlist({ email, plan, currency }),
    onSuccess: () => {
      toast.success("You're on the waitlist — we'll email you when payments open.");
      setEmail("");
    },
    onError: (err) => {
      const msg =
        err instanceof ApiError ? err.message : "Couldn't join the waitlist.";
      toast.error(msg);
    },
  });

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email) return;
    join.mutate();
  }

  return (
    <section className="mt-12">
      <Card id={`waitlist-${plan}`} className="bg-paper-white">
        <CardHeader>
          <CardTitle>Join the waitlist</CardTitle>
          <p className="text-sm text-ink-muted">
            Payment goes live after FYP. Reserve your email and we&apos;ll
            switch you on the day Pro and Elite become billable.
          </p>
        </CardHeader>
        <CardBody>
          <form
            onSubmit={onSubmit}
            className="grid gap-3 md:grid-cols-[1fr_auto_auto] md:items-end"
            data-testid="waitlist-form"
          >
            <div className="space-y-1.5">
              <Label htmlFor="waitlist-email">Email</Label>
              <Input
                id="waitlist-email"
                type="email"
                required
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="waitlist-plan">Plan</Label>
              <select
                id="waitlist-plan"
                value={plan}
                onChange={(e) => setPlan(e.target.value as "pro" | "elite")}
                className="h-11 w-full rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 text-[15px] text-ink"
              >
                <option value="pro">Pro</option>
                <option value="elite">Elite</option>
              </select>
            </div>
            <Button type="submit" loading={join.isPending}>
              Reserve my spot
            </Button>
          </form>
          <p className="mt-3 font-mono text-xs uppercase text-ink-muted">
            Currency: {currency}. No card required.
          </p>
        </CardBody>
      </Card>
    </section>
  );
}

function PartnerFooter() {
  return (
    <footer className="mt-16 border-t border-[var(--color-border)] pt-8 text-center text-sm text-ink-muted">
      Are you a university or Pakistani school?{" "}
      <Link href="/universities" className="text-ink underline-offset-4 hover:underline">
        Partner with us →
      </Link>
    </footer>
  );
}

// ---------------------------------------------------------------------------
// Status surfaces
// ---------------------------------------------------------------------------

function UpgradeSkeleton() {
  return (
    <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-80 w-full" />
      ))}
    </div>
  );
}

function ErrorBlock({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="mt-8 rounded-[16px] border border-[var(--color-border)] bg-paper-white p-6 text-center">
      <p className="text-ink">{message}</p>
      <Button onClick={onRetry} variant="secondary" className="mt-3">
        Retry
      </Button>
    </div>
  );
}
