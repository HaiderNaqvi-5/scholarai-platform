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
import { clerkEnabled } from "@/lib/auth/clerkAdapter";

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
      {/* Only mount the Clerk callback when Clerk is enabled. Without a
          publishable key the layout omits <ClerkProvider>, so rendering this
          component would throw — and break static prerender at build time
          (CI builds with no key). Mirrors the clerkEnabled gate used in
          AuthProvider / login / signup. */}
      {clerkEnabled && (
        <AuthenticateWithRedirectCallback
          signInFallbackRedirectUrl="/feed"
          signUpFallbackRedirectUrl="/onboarding"
        />
      )}
    </div>
  );
}
