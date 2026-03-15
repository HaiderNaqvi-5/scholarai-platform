"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { isApiError, useAuth } from "@/components/auth/auth-provider";
import { MarketingShell } from "@/components/layout/marketing-shell";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const nextPath = searchParams.get("next") ?? "/dashboard";

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace(nextPath);
    }
  }, [isAuthenticated, isLoading, nextPath, router]);

  return (
    <MarketingShell
      eyebrow="Authentication"
      title="Sign in to access your saved opportunities and workspace shell."
      description="This MVP authentication flow stays minimal: email, password, token-backed session, and protected workspace pages."
    >
      <section className="auth-grid">
        <form
          className="surface-card auth-form"
          data-testid="login-form"
          onSubmit={async (event) => {
            event.preventDefault();
            setError(null);
            setIsSubmitting(true);
            try {
              await login({ email, password });
              router.push(nextPath);
            } catch (caughtError) {
              setError(
                isApiError(caughtError)
                  ? caughtError.message
                  : "The login request failed.",
              );
            } finally {
              setIsSubmitting(false);
            }
          }}
        >
          <label className="form-field">
            <span className="route-card__label">Email</span>
            <input
              className="text-input"
              name="email"
              onChange={(event) => setEmail(event.target.value)}
              placeholder="student@example.com"
              type="email"
              value={email}
            />
          </label>
          <label className="form-field">
            <span className="route-card__label">Password</span>
            <input
              className="text-input"
              name="password"
              onChange={(event) => setPassword(event.target.value)}
              placeholder="At least 8 characters"
              type="password"
              value={password}
            />
          </label>
          {error ? <p className="form-error">{error}</p> : null}
          <button className="auth-link auth-link--primary" disabled={isSubmitting} type="submit">
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
        <article className="surface-panel">
          <p className="section-eyebrow">MVP auth posture</p>
          <h2 className="section-title">Simple account access, no role sprawl.</h2>
          <p className="body-copy">
            This slice adds the minimum useful session flow so students can save
            published opportunities and enter the dashboard workspace.
          </p>
          <Link className="nav-link" href="/signup">
            Create a new account
          </Link>
        </article>
      </section>
    </MarketingShell>
  );
}
