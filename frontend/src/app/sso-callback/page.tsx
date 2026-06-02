"use client";

/**
 * /sso-callback — return target for Clerk OAuth + magic-link flows.
 *
 * Two inbound flows land here:
 *  - OAuth/SSO: <AuthenticateWithRedirectCallback /> exchanges the provider
 *    token for a session, then redirects to the fallback URL.
 *  - Email magic-link: the clicked link carries `__clerk_status`; we call
 *    clerk.handleEmailLinkVerification() so the initiating tab's poll
 *    (createEmailLinkFlow) completes and the same-device tab redirects to
 *    /feed. AuthenticateWithRedirectCallback does NOT handle email links.
 *
 * The branded shell fronts a Fraunces "Signing you in…" while Clerk works.
 */

import { AuthenticateWithRedirectCallback, useClerk } from "@clerk/nextjs";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";
import { clerkEnabled } from "@/lib/auth/clerkAdapter";

function ClerkCallback() {
  const clerk = useClerk();
  // `__clerk_status` is present only on the clicked email magic-link return.
  // Derived from useSearchParams (consistent server + client → no hydration
  // mismatch, no setState-in-effect).
  const isEmailLink = useSearchParams().has("__clerk_status");

  useEffect(() => {
    if (isEmailLink) {
      void clerk
        .handleEmailLinkVerification({
          redirectUrlComplete: "/feed",
          redirectUrl: "/feed",
        })
        .catch(() => {
          window.location.assign("/login?error=link_expired");
        });
    }
  }, [clerk, isEmailLink]);

  // Email-link verification is handled imperatively above; nothing to mount.
  if (isEmailLink) return null;

  return (
    <AuthenticateWithRedirectCallback
      signInFallbackRedirectUrl="/feed"
      signUpFallbackRedirectUrl="/onboarding"
    />
  );
}

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
          publishable key the layout omits <ClerkProvider>, so calling
          useClerk() would throw — and break static prerender at build time
          (CI builds with no key). Mirrors the clerkEnabled gate used in
          AuthProvider / login / signup. Suspense satisfies useSearchParams'
          boundary requirement during prerender. */}
      {clerkEnabled && (
        <Suspense fallback={null}>
          <ClerkCallback />
        </Suspense>
      )}
    </div>
  );
}
