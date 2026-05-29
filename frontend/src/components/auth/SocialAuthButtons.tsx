"use client";

/**
 * SocialAuthButtons — 2x2 grid of OAuth buttons (Google / Microsoft /
 * Facebook / LinkedIn) above the email form on /login + /signup.
 *
 * Only renders in clerk mode (consumers gate on clerkEnabled). Brand
 * glyphs are inline SVG — no npm dep. Click → authenticateWithRedirect
 * → /sso-callback → final destination.
 */

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";
import {
  SOCIAL_PROVIDERS,
  useClerkSocialLogin,
  useClerkSocialSignup,
  type SocialProvider,
} from "@/lib/auth/clerkAdapter";

const PROVIDER_META: Record<
  SocialProvider,
  { label: string; Icon: React.FC<{ className?: string }> }
> = {
  google: { label: "Google", Icon: GoogleIcon },
  microsoft: { label: "Microsoft", Icon: MicrosoftIcon },
  facebook: { label: "Facebook", Icon: FacebookIcon },
  linkedin: { label: "LinkedIn", Icon: LinkedInIcon },
};

export function SocialAuthButtons({ mode }: { mode: "signin" | "signup" }) {
  const login = useClerkSocialLogin();
  const signup = useClerkSocialSignup();
  const start = mode === "signin" ? login : signup;
  const [pending, setPending] = useState<SocialProvider | null>(null);

  async function onClick(provider: SocialProvider) {
    if (pending) return;
    setPending(provider);
    try {
      await start(provider);
      // authenticateWithRedirect navigates away on success; we only reach
      // the next line on error.
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Couldn't start that sign-in.";
      toast.error(msg);
      setPending(null);
    }
  }

  return (
    <div className="space-y-3">
      <div className="grid gap-2 md:grid-cols-2">
        {SOCIAL_PROVIDERS.map((p) => {
          const { label, Icon } = PROVIDER_META[p];
          return (
            <Button
              key={p}
              type="button"
              variant="ghost"
              size="lg"
              className="w-full justify-center border border-[var(--color-border)] bg-paper-white hover:bg-paper-warm"
              onClick={() => onClick(p)}
              loading={pending === p}
              disabled={pending !== null && pending !== p}
            >
              <Icon className="size-4" />
              <span className="ml-2 text-[13px] font-medium text-ink-deep">{label}</span>
            </Button>
          );
        })}
      </div>
      <div className="relative flex items-center py-1">
        <hr className="flex-1 border-[var(--color-border-quiet)]" />
        <span className="px-3 font-mono text-[11px] uppercase tracking-[0.08em] text-ink-subtle">
          or continue with email
        </span>
        <hr className="flex-1 border-[var(--color-border-quiet)]" />
      </div>
    </div>
  );
}

/* ─── Inline brand glyphs ─────────────────────────────────────────── */
/* All icons use 24x24 viewBox; consumers control size via className. */

function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden>
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.75h3.57c2.08-1.92 3.28-4.74 3.28-8.07z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.75c-.99.66-2.25 1.06-3.71 1.06-2.87 0-5.3-1.94-6.16-4.55H2.18v2.84C4 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18A10.99 10.99 0 0 0 1 12c0 1.77.43 3.45 1.18 4.93l3.66-2.84z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 4 3.47 2.18 7.07l3.66 2.84C6.7 7.32 9.13 5.38 12 5.38z"
      />
    </svg>
  );
}

function MicrosoftIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden>
      <rect x="1" y="1" width="10" height="10" fill="#F25022" />
      <rect x="13" y="1" width="10" height="10" fill="#7FBA00" />
      <rect x="1" y="13" width="10" height="10" fill="#00A4EF" />
      <rect x="13" y="13" width="10" height="10" fill="#FFB900" />
    </svg>
  );
}

function FacebookIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden>
      <path
        fill="#1877F2"
        d="M24 12c0-6.63-5.37-12-12-12S0 5.37 0 12c0 5.99 4.39 10.95 10.13 11.85V15.47H7.08V12h3.05V9.41c0-3.01 1.79-4.67 4.53-4.67 1.31 0 2.69.23 2.69.23v2.96h-1.52c-1.49 0-1.96.93-1.96 1.88V12h3.33l-.53 3.47h-2.8v8.38C19.61 22.95 24 17.99 24 12z"
      />
    </svg>
  );
}

function LinkedInIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden>
      <path
        fill="#0A66C2"
        d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.86 0-2.14 1.45-2.14 2.94v5.67H9.34V9h3.42v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.72V1.72C24 .77 23.2 0 22.22 0z"
      />
    </svg>
  );
}
