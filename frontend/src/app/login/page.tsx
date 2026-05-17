"use client";

/**
 * /login — Sign in (Front-upgrade §6.6).
 *
 * Centered 380-wide form. Demo chips appear only outside production.
 * `Enter` submits. Rate-limit countdown surfaces on 429. CapsLock
 * warning when password field is focused.
 */

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState, useRef } from "react";
import { toast } from "sonner";
import { Eye, EyeOff, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth/AuthProvider";
import { ApiError } from "@/lib/api";
import { BRAND_DISPLAY_NAME } from "@/lib/brand";

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginInner />
    </Suspense>
  );
}

function LoginInner() {
  const auth = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get("next") || "/feed";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [capsLock, setCapsLock] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retrySeconds, setRetrySeconds] = useState(0);
  const retryTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const showDemo = process.env.NODE_ENV !== "production";

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

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (retrySeconds > 0) return;
    setSubmitting(true);
    setError(null);
    try {
      await auth.login({ email, password });
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

      <main id="main" className="flex flex-1 items-center justify-center px-6 py-16">
        <div className="w-full max-w-[380px]">
          <h1 className="font-display text-[32px] italic font-[400] leading-tight tracking-[-0.02em] text-ink-deep">
            Sign in
          </h1>

          <form onSubmit={onSubmit} className="mt-8 space-y-4" noValidate data-testid="login-form">
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
                <Link
                  href="/legal/privacy"
                  className="text-[12px] text-lapis underline underline-offset-2 hover:decoration-2"
                >
                  Forgot password?
                </Link>
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
          </form>

          {showDemo ? (
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
        </div>
      </main>
    </div>
  );
}
