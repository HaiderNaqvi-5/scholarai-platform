"use client";

/**
 * /login — Sign in (Front-upgrade §6.6).
 *
 * Centered 380-wide form. Demo chips appear only outside production.
 * `Enter` submits. Rate-limit countdown surfaces on 429. CapsLock
 * warning when password field is focused.
 *
 * Clerk mode adds:
 *   - Social OAuth row above the form (Google / Microsoft / Facebook / LinkedIn)
 *   - Magic-link mode toggle below the password field — switches the form to
 *     a "Send sign-in link" submit + "Check {email}" confirmation state.
 */

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState, useRef } from "react";
import { toast } from "sonner";
import { Eye, EyeOff, AlertTriangle, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth/AuthProvider";
import { ApiError } from "@/lib/api";
import { BRAND_DISPLAY_NAME } from "@/lib/brand";
import {
  clerkEnabled,
  useClerkLoginFlow,
  useClerkMagicLink,
} from "@/lib/auth/clerkAdapter";
import { SocialAuthButtons } from "@/components/auth/SocialAuthButtons";

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      {clerkEnabled ? <ClerkLoginInner /> : <LocalLoginInner />}
    </Suspense>
  );
}

function ClerkLoginInner() {
  const loginWithClerk = useClerkLoginFlow();
  const sendMagicLink = useClerkMagicLink();
  return (
    <LoginInner
      submit={async (email, password) => loginWithClerk({ email, password })}
      magicLink={sendMagicLink}
      social={<SocialAuthButtons mode="signin" />}
    />
  );
}

function LocalLoginInner() {
  const auth = useAuth();
  return (
    <LoginInner
      submit={async (email, password) => {
        await auth.login({ email, password });
      }}
    />
  );
}

type Mode = "password" | "magic-link" | "magic-sent";

function LoginInner({
  submit,
  magicLink,
  social,
}: {
  submit: (email: string, password: string) => Promise<void>;
  magicLink?: (email: string) => Promise<void>;
  social?: React.ReactNode;
}) {
  const auth = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  // H14: only honor same-origin relative paths. Reject protocol-relative
  // ("//evil.tld"), backslash ("/\\evil.tld") and absolute URLs so a crafted
  // ?next= cannot bounce the user to an attacker domain after login.
  const rawNext = params.get("next");
  const next =
    rawNext && rawNext.startsWith("/") && !rawNext.startsWith("//") && !rawNext.startsWith("/\\")
      ? rawNext
      : "/feed";

  const [mode, setMode] = useState<Mode>("password");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [capsLock, setCapsLock] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retrySeconds, setRetrySeconds] = useState(0);
  const [resendCooldown, setResendCooldown] = useState(0);
  const retryTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const showDemo = process.env.NODE_ENV !== "production" && !clerkEnabled;

  useEffect(() => {
    if (auth.status === "authed") router.replace(next);
  }, [auth.status, next, router]);

  useEffect(() => {
    if (retrySeconds <= 0) {
      if (retryTimer.current) clearInterval(retryTimer.current);
      return;
    }
    retryTimer.current = setInterval(() => setRetrySeconds((s) => Math.max(0, s - 1)), 1_000);
    return () => {
      if (retryTimer.current) clearInterval(retryTimer.current);
    };
  }, [retrySeconds]);

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const id = setInterval(() => setResendCooldown((s) => Math.max(0, s - 1)), 1_000);
    return () => clearInterval(id);
  }, [resendCooldown]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (retrySeconds > 0) return;
    setSubmitting(true);
    setError(null);
    try {
      await submit(email, password);
      router.replace(next);
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        setRetrySeconds(60);
        setError("Too many attempts. Try again in 60 seconds.");
      } else if (err instanceof ApiError && err.status === 401) {
        setError("Email or password is incorrect.");
      } else {
        const msg = err instanceof ApiError ? err.message : "Couldn't sign you in.";
        setError(msg);
        toast.error(msg);
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function onSendLink() {
    if (!magicLink || email.length < 3) return;
    setSubmitting(true);
    setError(null);
    try {
      await magicLink(email);
      setMode("magic-sent");
      setResendCooldown(30);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Couldn't send the link.";
      setError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  }

  async function onResendLink() {
    if (!magicLink || resendCooldown > 0) return;
    setError(null);
    try {
      await magicLink(email);
      setResendCooldown(30);
      toast.success("Link resent.");
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Couldn't resend the link.";
      setError(msg);
      toast.error(msg);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-ivory">
      <header className="border-b border-[var(--color-border-quiet)]">
        <div className="mx-auto flex max-w-[1200px] items-center justify-between px-6 py-4 md:px-12">
          <Link
            href="/"
            className="font-display text-[22px] italic font-[450] tracking-[-0.02em] text-ink-deep"
          >
            {BRAND_DISPLAY_NAME}
          </Link>
          <Link href="/signup" className="text-[13px] text-ink-muted hover:text-ink-deep">
            New here? Create an account
          </Link>
        </div>
      </header>

      <main id="main" className="mx-auto grid max-w-[1200px] gap-12 px-6 py-12 md:grid-cols-12 md:gap-16 md:px-12 md:py-20">
        {/* Editorial copy (md+) */}
        <section className="hidden md:col-span-5 md:block">
          <p className="font-mono text-[11px] uppercase tracking-[0.12em] text-ink-subtle">
            Welcome back
          </p>
          <h1 className="mt-4 font-display text-[48px] italic font-[400] leading-[1.05] tracking-[-0.02em] text-ink-deep">
            Your matches<br />are waiting.
          </h1>
          <p className="mt-5 max-w-[34ch] text-[16px] leading-[1.55] text-ink-muted">
            Sign back in to pick up your tracker, SOP drafts, and visa
            practice exactly where you left them.
          </p>
          <ul className="mt-10 space-y-4 text-[14px] text-ink-muted">
            <li className="flex gap-3">
              <ShieldCheck className="mt-0.5 size-4 shrink-0 text-validated" strokeWidth={1.5} />
              <span>Matches refresh against new scholarships every cycle.</span>
            </li>
            <li className="flex gap-3">
              <ShieldCheck className="mt-0.5 size-4 shrink-0 text-validated" strokeWidth={1.5} />
              <span>Your tracker, drafts, and rehearsals stay saved.</span>
            </li>
            <li className="flex gap-3">
              <ShieldCheck className="mt-0.5 size-4 shrink-0 text-validated" strokeWidth={1.5} />
              <span>PDPB-aligned. Your data stays yours.</span>
            </li>
          </ul>
        </section>

        {/* Form (full bleed on 375) */}
        <section className="md:col-span-7 md:max-w-[440px]">
          <h1 className="font-display text-[28px] italic font-[400] leading-tight tracking-[-0.02em] text-ink-deep md:hidden">
            Sign in
          </h1>

          {social && mode !== "magic-sent" ? <div className="mt-8">{social}</div> : null}

          {mode === "password" && (
            <form onSubmit={onSubmit} className={social ? "space-y-4" : "mt-8 space-y-4"} noValidate data-testid="login-form">
              <div>
                <Label htmlFor="email" className="mb-1.5 block text-[13px] font-medium text-ink-deep">
                  Email
                </Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoFocus
                />
              </div>

              <div>
                <div className="mb-1.5 flex items-center justify-between">
                  <Label htmlFor="password" className="text-[13px] font-medium text-ink-deep">
                    Password
                  </Label>
                  {magicLink ? (
                    <button
                      type="button"
                      onClick={() => {
                        setMode("magic-link");
                        setError(null);
                        setPassword("");
                      }}
                      className="text-[12px] text-lapis underline underline-offset-2 hover:decoration-2"
                    >
                      Forgot password?
                    </button>
                  ) : null}
                </div>
                <div className="relative">
                  <Input
                    id="password"
                    name="password"
                    type={showPw ? "text" : "password"}
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onKeyUp={(e) => setCapsLock(e.getModifierState("CapsLock"))}
                    onKeyDown={(e) => setCapsLock(e.getModifierState("CapsLock"))}
                    className="pr-12"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw((v) => !v)}
                    aria-label={showPw ? "Hide password" : "Show password"}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-ink-deep"
                  >
                    {showPw ? <EyeOff className="size-4" strokeWidth={1.5} /> : <Eye className="size-4" strokeWidth={1.5} />}
                  </button>
                </div>
                {capsLock ? (
                  <p className="mt-2 flex items-center gap-1.5 text-[12px] text-caution" role="alert">
                    <AlertTriangle className="size-3.5" strokeWidth={1.5} />
                    Caps Lock is on.
                  </p>
                ) : null}
              </div>

              {error ? (
                <p
                  role="alert"
                  className="rounded-[10px] border border-sindoor/30 bg-sindoor-soft px-3 py-2 text-[13px] text-sindoor"
                >
                  {error}
                  {retrySeconds > 0 ? (
                    <span className="ml-2 font-mono tabular-nums">{retrySeconds}s</span>
                  ) : null}
                </p>
              ) : null}

              <Button
                type="submit"
                loading={submitting}
                disabled={retrySeconds > 0}
                className="w-full"
                size="lg"
              >
                Sign in
              </Button>

              {magicLink ? (
                <button
                  type="button"
                  onClick={() => {
                    setMode("magic-link");
                    setError(null);
                    setPassword("");
                  }}
                  className="block w-full text-center text-[12px] text-lapis underline underline-offset-2 hover:decoration-2"
                >
                  Or email me a sign-in link
                </button>
              ) : null}
            </form>
          )}

          {mode === "magic-link" && (
            <div className={social ? "space-y-5" : "mt-8 space-y-5"}>
              <p className="text-[13px] text-ink-muted">
                We&apos;ll send a one-tap sign-in link to your email.
              </p>
              <div>
                <Label htmlFor="email-link" className="mb-1.5 block text-[13px] font-medium text-ink-deep">
                  Email
                </Label>
                <Input
                  id="email-link"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoFocus
                />
              </div>
              {error ? (
                <p role="alert" className="rounded-[10px] border border-sindoor/30 bg-sindoor-soft px-3 py-2 text-[13px] text-sindoor">
                  {error}
                </p>
              ) : null}
              <Button
                type="button"
                onClick={onSendLink}
                loading={submitting}
                disabled={email.length < 3}
                className="w-full"
                size="lg"
              >
                Send sign-in link
              </Button>
              <button
                type="button"
                onClick={() => {
                  setMode("password");
                  setError(null);
                }}
                className="block w-full text-center text-[12px] text-ink-muted hover:text-ink-deep"
              >
                Use password instead
              </button>
            </div>
          )}

          {mode === "magic-sent" && (
            <div className="mt-8 space-y-5">
              <p className="text-[13px] text-ink-muted">
                We sent a sign-in link to{" "}
                <span className="font-medium text-ink-deep">{email}</span>. Open
                it from this device to finish signing in.
              </p>
              {error ? (
                <p role="alert" className="rounded-[10px] border border-sindoor/30 bg-sindoor-soft px-3 py-2 text-[13px] text-sindoor">
                  {error}
                </p>
              ) : null}
              <button
                type="button"
                onClick={onResendLink}
                disabled={resendCooldown > 0}
                className="block w-full text-center text-[13px] text-lapis underline underline-offset-2 disabled:text-ink-subtle disabled:no-underline"
              >
                {resendCooldown > 0 ? `Resend link in ${resendCooldown}s` : "Resend link"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode("password");
                  setError(null);
                }}
                className="block w-full text-center text-[12px] text-ink-muted hover:text-ink-deep"
              >
                Use a different email
              </button>
            </div>
          )}

          {showDemo && mode === "password" ? (
            <div className="mt-6">
              <p className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
                Demo · dev only
              </p>
              <div className="mt-2 flex gap-2">
                <button
                  type="button"
                  className="flex-1 rounded-[10px] border border-[var(--color-border)] bg-paper-white px-3 py-2 text-[12px] text-ink-deep transition-colors hover:bg-paper-warm tap-target"
                  onClick={() => {
                    setEmail("student@example.com");
                    setPassword("strongpass1");
                  }}
                >
                  Student
                </button>
                <button
                  type="button"
                  className="flex-1 rounded-[10px] border border-[var(--color-border)] bg-paper-white px-3 py-2 text-[12px] text-ink-deep transition-colors hover:bg-paper-warm tap-target"
                  onClick={() => {
                    setEmail("admin@example.com");
                    setPassword("strongpass1");
                  }}
                >
                  Admin
                </button>
              </div>
            </div>
          ) : null}

          <p className="mt-8 text-center text-[13px] text-ink-muted">
            New here?{" "}
            <Link href="/signup" className="text-lapis underline underline-offset-2 hover:decoration-2">
              Create an account
            </Link>
          </p>
        </section>
      </main>
    </div>
  );
}
