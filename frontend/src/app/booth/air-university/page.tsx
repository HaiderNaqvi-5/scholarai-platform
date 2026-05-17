"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowRight, Copy, Check, ShieldCheck, Sparkles, FileSignature, Plane } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { BRAND_DISPLAY_NAME } from "@/lib/brand";

/**
 * Booth landing (Front-upgrade §6.2).
 *
 * Goal: convert a QR-scanning student at the Air University booth into
 * a signup with invite code pre-applied, in under 90 seconds. Mobile-
 * first. Single CTA. No nav. Trust footer with PDPB + trial deadline.
 *
 * Trial window: May 19 09:00 → May 26 23:59 PKT (UTC+5). After expiry,
 * the page replaces the value statement with an Explorer fallback CTA.
 *
 * Per-screen anti-slop bans: animated "Limited time!" badge, countdown
 * with milliseconds, balloon emoji, gradient on h1.
 */

const INVITE_CODE = "AIRU2026";
/** Trial window close in PKT (UTC+5). May 26 23:59 PKT = 18:59 UTC. */
const TRIAL_CLOSES_UTC = new Date("2026-05-26T18:59:00Z");

function getTrialState() {
  const now = new Date();
  if (now > TRIAL_CLOSES_UTC) return { expired: true, daysLeft: 0, hoursLeft: 0 };
  const msLeft = TRIAL_CLOSES_UTC.getTime() - now.getTime();
  const daysLeft = Math.floor(msLeft / 86_400_000);
  const hoursLeft = Math.floor((msLeft % 86_400_000) / 3_600_000);
  return { expired: false, daysLeft, hoursLeft };
}

export default function BoothAirUniversity() {
  const [state, setState] = useState(getTrialState);
  const [copied, setCopied] = useState(false);

  // Counter ticks only when <24 hours remain (§6.2 motion spec).
  useEffect(() => {
    if (state.expired || state.daysLeft >= 1) return;
    const id = setInterval(() => setState(getTrialState()), 1_000);
    return () => clearInterval(id);
  }, [state.expired, state.daysLeft]);

  const onCopyInvite = async () => {
    try {
      await navigator.clipboard.writeText(INVITE_CODE);
      setCopied(true);
      toast.success(`${INVITE_CODE} copied`);
      setTimeout(() => setCopied(false), 2_000);
    } catch {
      toast.error("Couldn't copy.");
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-ivory">
      {/* Co-mark header — never sticky on booth landing. */}
      <header className="border-b border-[var(--color-border-quiet)]">
        <div className="mx-auto flex max-w-[560px] items-center justify-between px-6 py-5">
          <Link
            href="/"
            className="font-display text-[20px] italic font-[450] tracking-[-0.02em] text-ink-deep"
          >
            {BRAND_DISPLAY_NAME}
          </Link>
          <div className="flex items-center gap-2">
            <div className="h-5 w-px bg-[var(--color-border)]" aria-hidden />
            <p className="font-mono text-[11px] uppercase tracking-[0.08em] text-ink-muted">
              × Air University
            </p>
          </div>
        </div>
      </header>

      <main id="main" className="flex flex-1 flex-col">
        <section className="mx-auto w-full max-w-[560px] flex-1 px-6 pt-12 pb-44 md:pt-16 md:pb-16">
          {/* H1 — Fraunces italic, max-w 12ch to force two-line wrap on phones */}
          <h1 className="font-display text-[40px] italic font-[400] leading-[1.05] tracking-[-0.02em] text-ink-deep md:text-[48px]">
            30 days of Pro,
            <br />
            free for Air U.
          </h1>

          {/* Invite chip + countdown */}
          <div className="mt-6 flex flex-col gap-3">
            <button
              type="button"
              onClick={onCopyInvite}
              className="group inline-flex w-fit items-center gap-2.5 rounded-[10px] border border-gold-leaf/40 bg-gold-soft px-3.5 py-2 transition-colors duration-[var(--motion-micro)] ease-[var(--ease-out)] hover:bg-gold-soft/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-ivory tap-target"
              aria-label={`Invite code ${INVITE_CODE}, tap to copy`}
            >
              <span className="font-mono text-[14px] font-semibold tracking-[0.08em] text-gold-leaf">
                {INVITE_CODE}
              </span>
              {copied ? (
                <Check className="size-4 text-validated" strokeWidth={1.5} />
              ) : (
                <Copy className="size-4 text-gold-leaf/80 transition-opacity group-hover:opacity-100" strokeWidth={1.5} />
              )}
            </button>

            {!state.expired ? (
              <p
                className="font-mono text-[13px] text-ink-muted tabular-nums"
                aria-live={state.daysLeft < 1 ? "polite" : "off"}
              >
                Trial closes May 26, 23:59 PKT —{" "}
                <span className="text-ink-deep">
                  {state.daysLeft > 0
                    ? `${state.daysLeft} day${state.daysLeft === 1 ? "" : "s"} left`
                    : `${state.hoursLeft} hour${state.hoursLeft === 1 ? "" : "s"} left`}
                </span>
              </p>
            ) : null}
          </div>

          <p className="mt-6 max-w-[40ch] text-[17px] leading-[1.55] text-ink-muted">
            Use code {INVITE_CODE} at signup. Free 30-day Pro trial for every
            Air University student. No payment required, no auto-renewal.
          </p>

          {/* Value bullets — mono numerals per anti-slop allow list */}
          {!state.expired ? (
            <ul className="mt-10 space-y-4">
              <ValueBullet
                icon={<Sparkles className="size-5" strokeWidth={1.5} />}
                count="20"
                title="fully-funded scholarships"
                detail="Match against Chevening, Fulbright, DAAD, Commonwealth, HEC Overseas, and 15 more."
              />
              <ValueBullet
                icon={<FileSignature className="size-5" strokeWidth={1.5} />}
                count="5"
                title="SOP drafts per month"
                detail="Pakistan-context paragraphs with return-intent framing. Edit, regenerate, export."
              />
              <ValueBullet
                icon={<Plane className="size-5" strokeWidth={1.5} />}
                count="70"
                title="visa questions"
                detail="UK · US · CA · DE. Country-tuned rubric and model answers."
              />
            </ul>
          ) : (
            <ExpiredFallback />
          )}

          {/* Single CTA — sticky on mobile, inline on md+ */}
          <div className="hidden md:mt-10 md:block">
            <Button asChild size="lg" className="w-full md:w-auto">
              <Link href={state.expired ? "/signup" : `/signup?invite=${INVITE_CODE}`}>
                {state.expired ? "Sign up free" : "Start now — 60 seconds"}
                <ArrowRight className="size-4" strokeWidth={1.5} />
              </Link>
            </Button>
          </div>

          {/* Trust footer */}
          <div className="mt-12 flex items-start gap-3 border-t border-[var(--color-border-quiet)] pt-6">
            <ShieldCheck className="mt-0.5 size-4 shrink-0 text-validated" strokeWidth={1.5} />
            <p className="text-[13px] leading-[1.55] text-ink-muted">
              We follow Pakistan&apos;s Personal Data Protection Bill. We never
              share your data without consent.{" "}
              <Link href="/legal/privacy" className="underline decoration-1 underline-offset-2 hover:decoration-2">
                Read the privacy notice
              </Link>
              .
            </p>
          </div>
        </section>
      </main>

      {/* Sticky CTA — mobile only */}
      <div className="sticky bottom-0 border-t border-[var(--color-border)] bg-ivory/95 px-6 py-4 backdrop-blur-md md:hidden">
        <Button asChild size="lg" className="w-full">
          <Link href={state.expired ? "/signup" : `/signup?invite=${INVITE_CODE}`}>
            {state.expired ? "Sign up free" : "Start now — 60 seconds"}
            <ArrowRight className="size-4" strokeWidth={1.5} />
          </Link>
        </Button>
      </div>
    </div>
  );
}

function ValueBullet({
  icon,
  count,
  title,
  detail,
}: {
  icon: React.ReactNode;
  count: string;
  title: string;
  detail: string;
}) {
  return (
    <li className="flex gap-4">
      <span
        aria-hidden
        className="flex size-10 shrink-0 items-center justify-center rounded-[10px] bg-paper-warm text-ink-deep"
      >
        {icon}
      </span>
      <div className="min-w-0">
        <p className="flex items-baseline gap-2">
          <span className="font-mono text-[20px] font-semibold tabular-nums text-ink-deep">
            {count}
          </span>
          <span className="text-[15px] font-medium text-ink-deep">{title}</span>
        </p>
        <p className="mt-1 text-[14px] leading-[1.55] text-ink-muted">{detail}</p>
      </div>
    </li>
  );
}

function ExpiredFallback() {
  return (
    <div className="mt-8 rounded-[18px] border border-[var(--color-border)] bg-paper-warm/60 p-5">
      <Badge tone="sindoor">Window closed</Badge>
      <p className="mt-3 text-[15px] leading-[1.55] text-ink-deep">
        The Air University trial window closed on May 26, 23:59 PKT.
      </p>
      <p className="mt-2 text-[14px] leading-[1.55] text-ink-muted">
        You can still sign up for Explorer — three matches, one SOP, three visa
        questions — free forever, no card required.
      </p>
    </div>
  );
}
