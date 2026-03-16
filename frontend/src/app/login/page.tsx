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
      eyebrow="Account access"
      title="Sign in to continue your scholarship planning."
      description="Use the same account to keep your shortlist, profile, and preparation workspaces connected."
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
          <p className="section-eyebrow">Why sign in</p>
          <h2 className="section-title">Keep your shortlist and profile in one place.</h2>
          <p className="body-copy">
            ScholarAI uses one lightweight account so saved opportunities,
            recommendations, and preparation work stay connected without adding
            unnecessary setup.
          </p>
          <Link className="nav-link" href="/signup">
            Create an account
          </Link>
        </article>
      </section>
    </MarketingShell>
  );
}
