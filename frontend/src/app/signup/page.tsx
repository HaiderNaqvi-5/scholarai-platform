"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { isApiError, useAuth } from "@/components/auth/auth-provider";
import { MarketingShell } from "@/components/layout/marketing-shell";

export default function SignupPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading, register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const nextPath = searchParams.get("next") ?? "/onboarding";

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace(nextPath);
    }
  }, [isAuthenticated, isLoading, nextPath, router]);

  return (
    <MarketingShell
      eyebrow="Create account"
      title="Create your ScholarAI account and keep the scholarship workflow connected."
      description="The account flow stays deliberately short so you can move straight into profile setup and recommendations."
    >
      <section className="auth-grid">
        <form
          className="surface-card auth-form"
          data-testid="signup-form"
          onSubmit={async (event) => {
            event.preventDefault();
            setError(null);
            setIsSubmitting(true);
            try {
              await register({ full_name: fullName, email, password });
              router.push(nextPath);
            } catch (caughtError) {
              setError(
                isApiError(caughtError)
                  ? caughtError.message
                  : "The signup request failed.",
              );
            } finally {
              setIsSubmitting(false);
            }
          }}
        >
          <label className="form-field">
            <span className="route-card__label">Full name</span>
            <input
              className="text-input"
              name="full_name"
              onChange={(event) => setFullName(event.target.value)}
              placeholder="Your name"
              type="text"
              value={fullName}
            />
          </label>
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
            {isSubmitting ? "Creating account..." : "Create account"}
          </button>
        </form>
        <article className="surface-panel">
          <p className="section-eyebrow">What this unlocks</p>
          <h2 className="section-title">Save opportunities, complete your profile, and return later.</h2>
          <p className="body-copy">
            The account gives your shortlist and preparation work a stable home.
            It does not introduce extra complexity beyond what the MVP needs.
          </p>
          <Link className="nav-link" href="/login">
            Already have an account?
          </Link>
        </article>
      </section>
    </MarketingShell>
  );
}
