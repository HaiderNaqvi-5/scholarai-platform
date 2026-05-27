"use client";

/**
 * ConnectedAccountsPanel — user-facing management of Clerk external accounts.
 *
 * Lists currently linked OAuth providers via @clerk/nextjs useUser().
 * Each row has a Disconnect button. Below, unlinked providers render
 * "Connect" buttons that call user.createExternalAccount → OAuth redirect
 * back through /sso-callback.
 *
 * Disconnect guard: refuses when removal would orphan the account
 * (i.e. last identification method). Clerk also enforces this server-side;
 * the client-side check is preemptive UX.
 *
 * Only mounted in clerk mode (consumer gates on clerkEnabled).
 */

import { useState } from "react";
import { useUser } from "@clerk/nextjs";
import type { OAuthStrategy } from "@clerk/types";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { SOCIAL_PROVIDERS, providerStrategy } from "@/lib/auth/clerkAdapter";

const PROVIDER_LABELS: Record<string, string> = {
  oauth_google: "Google",
  oauth_microsoft: "Microsoft",
  oauth_facebook: "Facebook",
  oauth_linkedin_oidc: "LinkedIn",
};

// Derive from clerkAdapter SOCIAL_PROVIDERS so enabling another provider
// only requires editing one array.
const ALL_STRATEGIES: OAuthStrategy[] = SOCIAL_PROVIDERS.map(providerStrategy);

export function ConnectedAccountsPanel() {
  const { user, isLoaded } = useUser();
  const [pending, setPending] = useState<string | null>(null);

  if (!isLoaded) {
    return <p className="text-[13px] text-ink-subtle">Loading…</p>;
  }
  if (!user) {
    return <p className="text-[13px] text-ink-subtle">Sign in to manage connected accounts.</p>;
  }

  const linked = user.externalAccounts;
  const linkedStrategies = new Set(linked.map((a) => `oauth_${a.provider}`));
  const unlinked = ALL_STRATEGIES.filter((s) => !linkedStrategies.has(s));
  const canDisconnect = linked.length + (user.passwordEnabled ? 1 : 0) > 1;

  async function disconnect(externalAccountId: string) {
    if (pending || !user) return;
    setPending(externalAccountId);
    try {
      const acc = user.externalAccounts.find((a) => a.id === externalAccountId);
      if (!acc) return;
      await acc.destroy();
      await user.reload();
      toast.success("Account disconnected.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Couldn't disconnect.");
    } finally {
      setPending(null);
    }
  }

  async function connect(strategy: OAuthStrategy) {
    if (pending || !user) return;
    setPending(strategy);
    try {
      await user.createExternalAccount({
        strategy,
        redirectUrl: `${window.location.origin}/sso-callback`,
      });
      // OAuth redirect navigates away on success.
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Couldn't start that connection.");
      setPending(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-display text-[20px] italic font-[400] text-ink-deep">
          Connected accounts
        </h3>
        <p className="mt-1 text-[13px] text-ink-muted">
          Sign in with any of these. You always need at least one way to log in.
        </p>
      </div>

      <div className="space-y-2">
        {linked.length === 0 ? (
          <p className="text-[13px] text-ink-subtle">No external accounts linked yet.</p>
        ) : (
          linked.map((acc) => (
            <div
              key={acc.id}
              className="flex items-center justify-between rounded-[10px] border border-[var(--color-border)] bg-paper-white px-4 py-3"
            >
              <div>
                <p className="text-[13px] font-medium text-ink-deep">
                  {PROVIDER_LABELS[`oauth_${acc.provider}`] ?? acc.provider}
                </p>
                <p className="text-[12px] text-ink-muted">{acc.emailAddress}</p>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => disconnect(acc.id)}
                loading={pending === acc.id}
                disabled={!canDisconnect || (pending !== null && pending !== acc.id)}
              >
                Disconnect
              </Button>
            </div>
          ))
        )}
      </div>

      {unlinked.length > 0 ? (
        <div className="space-y-2">
          <p className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
            Connect a new account
          </p>
          <div className="grid gap-2 md:grid-cols-2">
            {unlinked.map((s) => (
              <Button
                key={s}
                type="button"
                variant="ghost"
                size="md"
                className="w-full justify-start border border-[var(--color-border)] bg-paper-white"
                onClick={() => connect(s)}
                loading={pending === s}
                disabled={pending !== null && pending !== s}
              >
                + {PROVIDER_LABELS[s]}
              </Button>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
