"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { isApiError, useAuth } from "@/components/auth/auth-provider";
import { MarketingShell } from "@/components/layout/marketing-shell";

export default function SignupPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <MarketingShell
      eyebrow="Account setup"
      title="Create the smallest account needed to save opportunities and use the dashboard."
      description="ScholarAI keeps this slice intentionally lean: name, email, password, then direct entry into the authenticated workspace."
    >
      <section className="auth-grid">
        <form
          className="surface-card auth-form"
          onSubmit={async (event) => {
            event.preventDefault();
            setError(null);
            setIsSubmitting(true);
            try {
              await register({ full_name: fullName, email, password });
              router.push("/dashboard");
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
          <p className="section-eyebrow">Why this exists</p>
          <h2 className="section-title">Saved opportunities need an account owner.</h2>
          <p className="body-copy">
            Authentication is added here only because saved opportunities and
            the dashboard shell require a stable user identity.
          </p>
          <Link className="nav-link" href="/login">
            Already have an account?
          </Link>
        </article>
      </section>
    </MarketingShell>
  );
}
