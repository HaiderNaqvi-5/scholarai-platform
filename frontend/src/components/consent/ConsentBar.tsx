"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { endpoints, isPlanRequiredError } from "@/lib/api";
import type { ConsentState, ConsentType } from "@/lib/api/types";

const LOCAL_VERSIONS_KEY = "aidwise.consent_versions";
type LocalVersions = Partial<Record<ConsentType, string>>;

const REFRESH_INTERVAL_MS = 5 * 60 * 1000;

function readLocal(): LocalVersions {
  if (typeof window === "undefined") return {};
  try {
    const raw = localStorage.getItem(LOCAL_VERSIONS_KEY);
    return raw ? (JSON.parse(raw) as LocalVersions) : {};
  } catch {
    return {};
  }
}

function writeLocal(versions: LocalVersions) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(LOCAL_VERSIONS_KEY, JSON.stringify(versions));
  } catch {
    // ignore quota
  }
}

function findMismatch(state: ConsentState | null): { type: ConsentType; version: string } | null {
  if (!state) return null;
  const local = readLocal();
  for (const t of ["terms", "privacy"] as const) {
    const current = state.current_versions[t];
    if (!current) continue;
    const granted = state.records.find((r) => r.consent_type === t && r.granted);
    const localAgreed = local[t];
    if (!granted || granted.version !== current || localAgreed !== current) {
      return { type: t, version: current };
    }
  }
  return null;
}

const TYPE_LABEL: Record<ConsentType, string> = {
  terms: "Terms of Service",
  privacy: "Privacy Notice",
  marketing: "Marketing",
  b2b_share: "B2B sharing",
  cookies: "Cookie policy",
  aup: "Acceptable use",
};

/**
 * ConsentBar — Front-upgrade §5.4 + §6.4.
 *
 * Sticky bottom bar that appears only when the user is signed in AND
 * their latest grant for `terms` / `privacy` does not match the current
 * server version. POSTs `/privacy/consent` on confirm. Silent (returns
 * null) for public / signed-out users.
 */
export function ConsentBar() {
  const [state, setState] = useState<ConsentState | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const load = useCallback(async () => {
    try {
      const s = await endpoints.legal.consentState();
      setState(s);
    } catch (err) {
      // Unauthenticated / network = ignore. We never block the page.
      if (!(err as { status?: number })?.status) return;
    }
  }, []);

  useEffect(() => {
    /* eslint-disable-next-line react-hooks/set-state-in-effect */
    load();
    const id = window.setInterval(load, REFRESH_INTERVAL_MS);
    return () => window.clearInterval(id);
  }, [load]);

  const mismatch = findMismatch(state);
  if (dismissed || !mismatch) return null;

  const handleAgree = async () => {
    setSubmitting(true);
    try {
      const next = await endpoints.legal.grant({
        consent_type: mismatch.type,
        version: mismatch.version,
        granted: true,
      });
      const local = readLocal();
      writeLocal({ ...local, [mismatch.type]: mismatch.version });
      setState(next);
      toast.success(`Agreed to ${TYPE_LABEL[mismatch.type]} v${mismatch.version}`);
    } catch (err) {
      if (isPlanRequiredError(err)) {
        toast.error(err.detail.message);
      } else {
        toast.error("Couldn't record your consent. Try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      role="region"
      aria-label="Consent action"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-[var(--color-border)] bg-[var(--color-paper-warm)] shadow-[var(--shadow-raised)]"
    >
      <div className="mx-auto flex max-w-[1200px] flex-col gap-3 px-6 py-4 md:flex-row md:items-center md:gap-6 md:px-12 md:py-4">
        <p className="text-[13px] leading-[1.55] text-ink md:flex-1">
          Version {mismatch.version} of {TYPE_LABEL[mismatch.type]} is in effect. Please review and agree.
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setDismissed(true)}
            aria-label="Dismiss for this session"
          >
            Later
          </Button>
          <Button
            asChild
            variant="secondary"
            size="sm"
          >
            <a href={`/legal/${mismatch.type}`}>Read</a>
          </Button>
          <Button size="sm" onClick={handleAgree} loading={submitting}>
            I agree to version {mismatch.version}
          </Button>
        </div>
      </div>
    </div>
  );
}
