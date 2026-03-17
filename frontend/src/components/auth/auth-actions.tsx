"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";

export function AuthActions() {
  const router = useRouter();
  const { currentUser, isAuthenticated, isLoading, logout } = useAuth();

  if (isLoading) {
    return <div className="auth-actions auth-actions--loading" />;
  }

  if (!isAuthenticated) {
    return (
      <div className="auth-actions">
        <Link className="nav-link nav-link--quiet" href="/login">
          Sign in
        </Link>
        <Link className="auth-link auth-link--primary" href="/signup">
          Create account
        </Link>
      </div>
    );
  }

  return (
    <div className="auth-actions">
      <div className="auth-chip">
        <span className="auth-chip__label">Signed in</span>
        <strong>{currentUser?.full_name ?? "ScholarAI user"}</strong>
      </div>
      <Link className="nav-link nav-link--quiet" href="/dashboard">
        Dashboard
      </Link>
      {currentUser?.role === "admin" ? (
        <Link className="nav-link nav-link--quiet" href="/curation">
          Curation
        </Link>
      ) : null}
      <button
        className="auth-link auth-link--secondary"
        onClick={() => {
          logout();
          router.push("/login");
        }}
        type="button"
      >
        Sign out
      </button>
    </div>
  );
}
