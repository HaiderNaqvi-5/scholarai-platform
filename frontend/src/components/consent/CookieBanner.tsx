"use client";

/**
 * CookieBanner (Front-upgrade §4.3 + §6.23 + §5.4).
 *
 * Bottom sheet on first visit only. Three buttons:
 *   - "Accept all"            : sets all categories to true
 *   - "Reject non-essential"  : only essential remains true
 *   - "Customize"             : opens CookiePreferences dialog
 *
 * Choice persists to localStorage `aidwise.cookie_consent`. Once set,
 * the banner never renders again unless the user clears it from
 * /settings → Privacy.
 *
 * Anti-slop: no "We value your privacy 🍪" theatrics. No full-screen
 * scrim. Sheet sits below content with a hairline top border.
 */

import { useEffect, useState } from "react";
import { Cookie, X } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

const STORAGE_KEY = "aidwise.cookie_consent";

export type CookieConsent = {
  essential: true;
  analytics: boolean;
  marketing: boolean;
  b2b: boolean;
  agreed_at: string;
};

export function readConsent(): CookieConsent | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as CookieConsent;
  } catch {
    return null;
  }
}

export function writeConsent(consent: Omit<CookieConsent, "essential" | "agreed_at">) {
  if (typeof window === "undefined") return;
  const full: CookieConsent = {
    essential: true,
    analytics: consent.analytics,
    marketing: consent.marketing,
    b2b: consent.b2b,
    agreed_at: new Date().toISOString(),
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(full));
  window.dispatchEvent(new CustomEvent("aidwise:consent-changed", { detail: full }));
}

export function CookieBanner() {
  /* Default to false so SSR matches initial CSR — the banner appears once
   * the effect below confirms localStorage has no consent record. The
   * one-tick delay is acceptable: consent UX never fires on first paint. */
  const [show, setShow] = useState(false);
  const [openPrefs, setOpenPrefs] = useState(false);

  useEffect(() => {
    /* eslint-disable-next-line react-hooks/set-state-in-effect */
    setShow(readConsent() === null);
  }, []);

  if (!show && !openPrefs) return null;

  return (
    <>
      {show && !openPrefs ? (
        <div
          role="region"
          aria-label="Cookie consent"
          className="fade-up fixed inset-x-0 bottom-0 z-40 border-t border-[var(--color-border)] bg-paper-white shadow-[var(--shadow-raised)]"
        >
          <div className="mx-auto flex max-w-[1200px] flex-col gap-4 px-6 py-4 md:flex-row md:items-center md:gap-6 md:px-12 md:py-5">
            <div className="flex items-start gap-3 md:flex-1">
              <Cookie className="mt-0.5 size-5 shrink-0 text-ink-deep" strokeWidth={1.5} />
              <p className="text-[13px] leading-[1.55] text-ink-muted">
                We use essential cookies to keep you signed in. With your permission,
                we also measure how you use the app to improve matches.{" "}
                <Link
                  href="/legal/cookie"
                  className="text-lapis underline underline-offset-2 hover:decoration-2"
                >
                  Cookie policy
                </Link>
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setOpenPrefs(true)}
                aria-haspopup="dialog"
              >
                Customize
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  writeConsent({ analytics: false, marketing: false, b2b: false });
                  setShow(false);
                }}
              >
                Reject non-essential
              </Button>
              <Button
                size="sm"
                onClick={() => {
                  writeConsent({ analytics: true, marketing: true, b2b: false });
                  setShow(false);
                }}
              >
                Accept all
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      {openPrefs ? (
        <CookiePreferences
          onClose={() => setOpenPrefs(false)}
          onSave={(c) => {
            writeConsent(c);
            setShow(false);
            setOpenPrefs(false);
          }}
        />
      ) : null}
    </>
  );
}

function CookiePreferences({
  onClose,
  onSave,
}: {
  onClose: () => void;
  onSave: (c: { analytics: boolean; marketing: boolean; b2b: boolean }) => void;
}) {
  const existing = readConsent();
  const [analytics, setAnalytics] = useState(existing?.analytics ?? false);
  const [marketing, setMarketing] = useState(existing?.marketing ?? false);
  const [b2b, setB2b] = useState(existing?.b2b ?? false);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="cookie-prefs-title"
      className="fixed inset-0 z-50 flex items-end justify-center bg-[var(--color-scrim)] px-4 py-6 md:items-center"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-[480px] rounded-[22px] border border-[var(--color-border)] bg-paper-white p-6 md:p-7">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2
              id="cookie-prefs-title"
              className="font-display text-[24px] italic font-[450] leading-tight text-ink-deep"
            >
              Cookie preferences
            </h2>
            <p className="mt-2 text-[14px] text-ink-muted">
              Choose what you allow. Essential cookies keep you signed in and cannot be turned off.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close preferences"
            className="rounded-[10px] p-2 text-ink-muted hover:bg-paper-warm hover:text-ink-deep tap-target"
          >
            <X className="size-4" strokeWidth={1.5} />
          </button>
        </div>

        <ul className="mt-6 divide-y divide-[var(--color-border-quiet)]">
          <PrefRow
            id="pref-essential"
            label="Essential"
            description="Sign-in, session, security. Always on."
            checked
            disabled
          />
          <PrefRow
            id="pref-analytics"
            label="Analytics"
            description="Anonymous usage telemetry. Helps us improve match quality."
            checked={analytics}
            onChange={setAnalytics}
          />
          <PrefRow
            id="pref-marketing"
            label="Marketing"
            description="Email me when scholarships matching my profile open."
            checked={marketing}
            onChange={setMarketing}
          />
          <PrefRow
            id="pref-b2b"
            label="Institution sharing"
            description="Allow Pro+ to share your profile with universities that have signed a DPA."
            checked={b2b}
            onChange={setB2b}
          />
        </ul>

        <div className="mt-6 flex items-center justify-end gap-2">
          <Button variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={() => onSave({ analytics, marketing, b2b })}
          >
            Save preferences
          </Button>
        </div>
      </div>
    </div>
  );
}

function PrefRow({
  id,
  label,
  description,
  checked,
  onChange,
  disabled,
}: {
  id: string;
  label: string;
  description: string;
  checked: boolean;
  onChange?: (v: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <li className="flex items-start justify-between gap-4 py-3.5">
      <div className="min-w-0">
        <p className="text-[14px] font-medium text-ink-deep">{label}</p>
        <p className="mt-1 text-[12px] leading-[1.5] text-ink-muted">{description}</p>
      </div>
      <label
        htmlFor={id}
        className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full transition-colors ${
          disabled ? "bg-paper-edge opacity-60" : checked ? "bg-lapis" : "bg-paper-edge"
        }`}
      >
        <input
          id={id}
          type="checkbox"
          checked={checked}
          disabled={disabled}
          onChange={(e) => onChange?.(e.target.checked)}
          className="peer sr-only"
        />
        <span
          aria-hidden
          className={`size-4 rounded-full bg-paper-white shadow transition-transform ${
            checked ? "translate-x-[18px]" : "translate-x-0.5"
          }`}
        />
      </label>
    </li>
  );
}
