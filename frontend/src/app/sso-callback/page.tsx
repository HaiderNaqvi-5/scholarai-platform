"use client";

/**
 * /sso-callback — return target for Clerk OAuth + magic-link flows.
 *
 * <AuthenticateWithRedirectCallback /> exchanges the inbound token from
 * the provider for an active Clerk session, then redirects to the
 * `redirectUrlComplete` originally passed to authenticateWithRedirect
 * (`/feed` for sign-in, `/onboarding` for sign-up). The branded shell
 * fronts a Fraunces "Signing you in…" while Clerk does the swap.
 */

import { AuthenticateWithRedirectCallback } from "@clerk/nextjs";

export default function SSOCallbackPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-ivory">
      <div className="text-center">
        <p className="font-display text-[28px] italic font-[400] tracking-[-0.02em] text-ink-deep">
          Signing you in…
        </p>
        <p className="mt-2 font-mono text-[11px] uppercase tracking-[0.08em] text-ink-subtle">
          Verifying your account
        </p>
      </div>
      <AuthenticateWithRedirectCallback />
    </div>
  );
}
